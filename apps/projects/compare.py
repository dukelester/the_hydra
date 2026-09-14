from decimal import Decimal

from django.db.models import Count, Q, Sum

from apps.core.services.coverage import calculate_evidence_coverage
from apps.projects.models import Project, ProjectStatus


def format_budget(amount, currency="KES"):
    if amount is None:
        return "Information unavailable"
    value = f"{Decimal(amount):,.0f}"
    if currency == "KES":
        return f"KSh {value}"
    return f"{currency} {value}"


def project_compare_rows(projects):
    rows = []
    for project in projects:
        coverage = calculate_evidence_coverage(project)
        rows.append(
            {
                "project": project,
                "coverage": coverage,
            }
        )
    return rows


def county_rankings():
    rows = list(
        Project.objects.values("county")
        .annotate(
            project_count=Count("id"),
            total_budget=Sum("allocated_amount"),
            delayed_count=Count("id", filter=Q(status=ProjectStatus.DELAYED)),
            completed_count=Count("id", filter=Q(status=ProjectStatus.COMPLETED)),
            in_progress_count=Count("id", filter=Q(status=ProjectStatus.IN_PROGRESS)),
            unknown_count=Count("id", filter=Q(status=ProjectStatus.UNKNOWN)),
        )
        .order_by("-total_budget", "-project_count", "county")
    )
    ranked = []
    for index, row in enumerate(rows, start=1):
        count = row["project_count"] or 0
        delayed = row["delayed_count"] or 0
        ranked.append(
            {
                **row,
                "rank": index,
                "formatted_budget": format_budget(row["total_budget"]),
                "delayed_share": round((delayed / count) * 100) if count else 0,
                "completed_share": round(((row["completed_count"] or 0) / count) * 100) if count else 0,
            }
        )
    return ranked


def county_compare_rows(names):
    names = [name for name in names if name]
    rankings = {row["county"]: row for row in county_rankings()}
    return [rankings[name] for name in names if name in rankings]


def status_totals():
    counts = dict(
        Project.objects.values("status")
        .annotate(total=Count("id"))
        .values_list("status", "total")
    )
    return [
        {
            "status": value,
            "label": label,
            "count": counts.get(value, 0),
        }
        for value, label in ProjectStatus.choices
    ]


def ranking_highlights(rankings):
    if not rankings:
        return {}
    total_budget = sum((row["total_budget"] or Decimal("0")) for row in rankings)
    return {
        "highest_budget": rankings[0],
        "most_delayed": max(rankings, key=lambda row: (row["delayed_share"], row["delayed_count"])),
        "most_projects": max(rankings, key=lambda row: row["project_count"]),
        "county_count": len(rankings),
        "project_count": sum(row["project_count"] for row in rankings),
        "total_budget": format_budget(total_budget),
    }
