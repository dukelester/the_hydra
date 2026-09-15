from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Q, Value, When

from apps.core.governance import normalize_country
from apps.policies.models import Policy
from apps.projects.models import Institution, Project
from apps.sources.models import Evidence, SourceDocument

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
    country="",
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
        "country": country or "",
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

    country = normalize_country(country)

    project_qs = _project_queryset(query, county, status, category, suggest, country) if include_projects else Project.objects.none()
    institution_qs = _institution_queryset(query, suggest, country) if include_institutions else Institution.objects.none()
    policy_qs = _policy_queryset(query, suggest, country) if include_policies else Policy.objects.none()
    document_qs = _document_queryset(query, suggest, country) if include_documents else SourceDocument.objects.none()

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
        "country": country or "",
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


def _project_queryset(query, county, status, category, suggest, country=""):
    country = normalize_country(country)
    indexed = (
        Q(name__icontains=query)
        | Q(slug__icontains=query)
        | Q(county__icontains=query)
        | Q(constituency__icontains=query)
        | Q(ward__icontains=query)
        | Q(location__icontains=query)
        | Q(contractor__icontains=query)
        | Q(financial_year__icontains=query)
        | Q(institution__name__icontains=query)
    )
    if not suggest:
        indexed |= Q(description__icontains=query)

    qs = Project.objects.select_related("institution").filter(indexed, country=country)
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
            (Q(constituency__iexact=query), 68),
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


def _institutions_for_country(qs, country):
    country = normalize_country(country)
    return qs.filter(
        Exists(Project.objects.filter(country=country, institution_id=OuterRef("pk")))
    )


def _policies_for_country(qs, country):
    country = normalize_country(country)
    via_institution = Project.objects.filter(country=country, institution_id=OuterRef("institution_id"))
    via_document = Project.objects.filter(country=country, source_documents=OuterRef("source_document_id"))
    return qs.filter(Q(Exists(via_institution)) | Q(Exists(via_document)))


def _documents_for_country(qs, country):
    country = normalize_country(country)
    country_institutions = Project.objects.filter(country=country).values("institution_id")
    in_project = Project.objects.filter(country=country, source_documents=OuterRef("pk"))
    in_evidence = Evidence.objects.filter(project__country=country, source_document_id=OuterRef("pk"))
    in_policy = Policy.objects.filter(
        source_document_id=OuterRef("pk"),
        institution_id__in=country_institutions,
    )
    return qs.filter(Q(Exists(in_project)) | Q(Exists(in_evidence)) | Q(Exists(in_policy)))


def _institution_queryset(query, suggest=False, country=""):
    country = normalize_country(country)
    match = Q(name__icontains=query) | Q(location__icontains=query)
    if not suggest:
        match |= Q(description__icontains=query)
    qs = _institutions_for_country(Institution.objects.filter(match), country).annotate(
        project_count=Count("projects", filter=Q(projects__country=country), distinct=True)
    )
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


def _policy_queryset(query, suggest=False, country=""):
    match = Q(title__icontains=query) | Q(institution__name__icontains=query)
    if not suggest:
        match |= Q(description__icontains=query)
    qs = _policies_for_country(Policy.objects.select_related("institution").filter(match), country)
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


def _document_queryset(query, suggest=False, country=""):
    match = (
        Q(title__icontains=query)
        | Q(publisher__icontains=query)
        | Q(original_filename__icontains=query)
    )
    if not suggest:
        match |= Q(description__icontains=query) | Q(extracted_text__icontains=query)
    qs = _documents_for_country(SourceDocument.objects.filter(match), country)
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


def project_search_queryset(query, county="", status="", category="", country=""):
    """Ranked project queryset for list pages and full search."""
    country = normalize_country(country)
    query = normalize_query(query)
    if not query:
        qs = Project.objects.select_related("institution").filter(country=country)
        if county:
            qs = qs.filter(county__iexact=county)
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)
        return qs.order_by("name")
    return _project_queryset(query, county, status, category, suggest=False, country=country)


def document_search_queryset(query, country=""):
    """Documents by name, filename, or extracted full text."""
    query = normalize_query(query)
    if not query:
        return _documents_for_country(SourceDocument.objects.all(), country)
    return _document_queryset(query, suggest=False, country=country)


def institution_search_queryset(query, country=""):
    query = normalize_query(query)
    if not query:
        country = normalize_country(country)
        return _institutions_for_country(
            Institution.objects.annotate(
                project_count=Count("projects", filter=Q(projects__country=country), distinct=True)
            ),
            country,
        ).order_by("name")
    return _institution_queryset(query, suggest=False, country=country)


def policy_search_queryset(query, country=""):
    query = normalize_query(query)
    if not query:
        return _policies_for_country(Policy.objects.select_related("institution"), country)
    return _policy_queryset(query, suggest=False, country=country)
