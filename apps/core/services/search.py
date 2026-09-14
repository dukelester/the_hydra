from django.db.models import Case, IntegerField, Q, Value, When

from apps.policies.models import Policy
from apps.projects.models import Institution, Project
from apps.sources.models import SourceDocument

MIN_LIVE_QUERY = 2
MAX_QUERY_LENGTH = 120


def normalize_query(query):
    return " ".join((query or "").split())[:MAX_QUERY_LENGTH]


def search_civic_data(
    query,
    *,
    limit=8,
    kind="all",
    county="",
    status="",
    category="",
    suggest=False,
):
    """
    Ranked civic search.

    Live/suggest mode only hits indexed fields (name, place, contractor,
    institution). Full search also scans descriptions. Counts are real
    queryset counts, not the size of the returned slice.
    """
    query = normalize_query(query)
    empty = {
        "query": query,
        "kind": kind or "all",
        "county": county or "",
        "status": status or "",
        "category": category or "",
        "suggest": suggest,
        "too_short": False,
        "projects": [],
        "institutions": [],
        "policies": [],
        "documents": [],
        "project_count": 0,
        "institution_count": 0,
        "policy_count": 0,
        "document_count": 0,
        "total": 0,
    }
    if not query:
        return empty
    if suggest and len(query) < MIN_LIVE_QUERY:
        empty["too_short"] = True
        return empty

    kind = (kind or "all").lower()
    include_projects = kind in {"all", "projects"}
    include_institutions = kind in {"all", "institutions"}
    include_policies = kind in {"all", "policies"}
    include_documents = kind in {"all", "documents"}
    if suggest and kind == "all":
        include_documents = True

    project_qs = _project_queryset(query, county, status, category, suggest) if include_projects else Project.objects.none()
    institution_qs = _institution_queryset(query, suggest) if include_institutions else Institution.objects.none()
    policy_qs = _policy_queryset(query, suggest) if include_policies else Policy.objects.none()
    document_qs = _document_queryset(query, suggest) if include_documents else SourceDocument.objects.none()

    project_count = project_qs.count() if include_projects else 0
    institution_count = institution_qs.count() if include_institutions else 0
    policy_count = policy_qs.count() if include_policies else 0
    document_count = document_qs.count() if include_documents else 0

    return {
        "query": query,
        "kind": kind,
        "county": county or "",
        "status": status or "",
        "category": category or "",
        "suggest": suggest,
        "too_short": False,
        "projects": list(project_qs[:limit]) if include_projects else [],
        "institutions": list(institution_qs[:limit]) if include_institutions else [],
        "policies": list(policy_qs[:limit]) if include_policies else [],
        "documents": list(document_qs[:limit]) if include_documents else [],
        "project_count": project_count,
        "institution_count": institution_count,
        "policy_count": policy_count,
        "document_count": document_count,
        "total": project_count + institution_count + policy_count + document_count,
    }


def _rank(*pairs, default=5):
    whens = [When(condition, then=Value(score)) for condition, score in pairs]
    return Case(*whens, default=Value(default), output_field=IntegerField())


def _project_queryset(query, county, status, category, suggest):
    indexed = (
        Q(name__icontains=query)
        | Q(slug__icontains=query)
        | Q(county__icontains=query)
        | Q(ward__icontains=query)
        | Q(location__icontains=query)
        | Q(contractor__icontains=query)
        | Q(financial_year__icontains=query)
        | Q(institution__name__icontains=query)
    )
    if not suggest:
        indexed |= Q(description__icontains=query)

    qs = Project.objects.select_related("institution").filter(indexed)
    if county:
        qs = qs.filter(county__iexact=county)
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category=category)

    qs = qs.annotate(
        rank=_rank(
            (Q(name__iexact=query), 100),
            (Q(name__istartswith=query), 85),
            (Q(county__iexact=query), 70),
            (Q(ward__iexact=query), 65),
            (Q(name__icontains=query), 50),
            (Q(institution__name__icontains=query), 40),
            (Q(contractor__icontains=query), 30),
            (Q(county__icontains=query) | Q(location__icontains=query), 25),
        )
    ).order_by("-rank", "name")
    if suggest:
        qs = qs.defer("description")
    return qs


def _institution_queryset(query, suggest=False):
    match = Q(name__icontains=query) | Q(location__icontains=query)
    if not suggest:
        match |= Q(description__icontains=query)
    qs = Institution.objects.filter(match)
    qs = qs.annotate(
        rank=_rank(
            (Q(name__iexact=query), 100),
            (Q(name__istartswith=query), 85),
            (Q(name__icontains=query), 50),
            (Q(location__icontains=query), 30),
        )
    ).order_by("-rank", "name")
    if suggest:
        qs = qs.defer("description")
    return qs


def _policy_queryset(query, suggest=False):
    match = Q(title__icontains=query) | Q(institution__name__icontains=query)
    if not suggest:
        match |= Q(description__icontains=query)
    qs = Policy.objects.select_related("institution").filter(match)
    qs = qs.annotate(
        rank=_rank(
            (Q(title__iexact=query), 100),
            (Q(title__istartswith=query), 85),
            (Q(title__icontains=query), 50),
        )
    ).order_by("-rank", "title")
    if suggest:
        qs = qs.defer("description")
    return qs


def _document_queryset(query, suggest=False):
    match = (
        Q(title__icontains=query)
        | Q(publisher__icontains=query)
        | Q(original_filename__icontains=query)
    )
    if not suggest:
        match |= Q(description__icontains=query) | Q(extracted_text__icontains=query)
    qs = SourceDocument.objects.filter(match)
    qs = qs.annotate(
        rank=_rank(
            (Q(title__iexact=query), 100),
            (Q(original_filename__iexact=query), 95),
            (Q(title__istartswith=query), 85),
            (Q(original_filename__istartswith=query), 80),
            (Q(title__icontains=query), 50),
            (Q(original_filename__icontains=query), 45),
            (Q(publisher__icontains=query), 30),
            (Q(extracted_text__icontains=query), 18),
        )
    ).order_by("-rank", "title")
    if suggest:
        qs = qs.defer("description", "extracted_text")
    return qs


def project_search_queryset(query, county="", status="", category=""):
    """Ranked project queryset for list pages and full search."""
    query = normalize_query(query)
    if not query:
        qs = Project.objects.select_related("institution")
        if county:
            qs = qs.filter(county__iexact=county)
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)
        return qs.order_by("name")
    return _project_queryset(query, county, status, category, suggest=False)


def document_search_queryset(query):
    """Documents by name, filename, or extracted full text."""
    query = normalize_query(query)
    if not query:
        return SourceDocument.objects.all()
    return _document_queryset(query, suggest=False)
