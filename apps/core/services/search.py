from django.db.models import Q

from apps.policies.models import Policy
from apps.projects.models import Institution, Project
from apps.sources.models import SourceDocument


def search_civic_data(query, *, limit=8):
    """Search projects, institutions, policies, and source documents."""
    query = (query or "").strip()
    if not query:
        return {
            "query": query,
            "projects": [],
            "institutions": [],
            "policies": [],
            "documents": [],
            "total": 0,
        }

    projects = list(
        Project.objects.select_related("institution").filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(county__icontains=query)
            | Q(ward__icontains=query)
            | Q(location__icontains=query)
            | Q(contractor__icontains=query)
            | Q(financial_year__icontains=query)
            | Q(institution__name__icontains=query)
        )[:limit]
    )
    institutions = list(
        Institution.objects.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
        )[:limit]
    )
    policies = list(
        Policy.objects.select_related("institution").filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(institution__name__icontains=query)
        )[:limit]
    )
    documents = list(
        SourceDocument.objects.filter(
            Q(title__icontains=query)
            | Q(publisher__icontains=query)
            | Q(description__icontains=query)
        )[:limit]
    )
    return {
        "query": query,
        "projects": projects,
        "institutions": institutions,
        "policies": policies,
        "documents": documents,
        "total": len(projects) + len(institutions) + len(policies) + len(documents),
    }
