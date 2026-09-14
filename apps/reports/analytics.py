from decimal import Decimal

from django.db.models import Count, Sum

from apps.core.services.coverage import calculate_evidence_coverage
from apps.projects.compare import county_rankings, format_budget
from apps.projects.models import BudgetAllocation, Project, ProjectCategory, ProjectStatus


def _share(part, whole):
    if not whole:
        return 0
    return round((part / whole) * 100)


def _bar_width(amount, peak):
    if not peak:
        return 0
    return round(float((amount or Decimal("0")) / peak) * 100, 1)


def decorate_county_charts(rankings):
    peak = max((row["total_budget"] or Decimal("0")) for row in rankings) if rankings else Decimal("0")
    decorated = []
    for row in rankings:
        count = row["project_count"] or 0
        completed = row["completed_count"] or 0
        in_progress = row["in_progress_count"] or 0
        delayed = row["delayed_count"] or 0
        other = max(count - completed - in_progress - delayed, 0)
        budget = row["total_budget"] or Decimal("0")
        decorated.append(
            {
                **row,
                "other_count": other,
                "in_progress_share": _share(in_progress, count),
                "other_share": _share(other, count),
                "budget_width": _bar_width(budget, peak),
                "completed_width": _share(completed, count),
                "progress_width": _share(in_progress, count),
                "delayed_width": _share(delayed, count),
                "other_width": _share(other, count),
            }
        )
    return decorated


def category_chart_rows(county=""):
    qs = Project.objects.all()
    if county:
        qs = qs.filter(county__iexact=county)
    raw = list(
        qs.values("category").annotate(
            project_count=Count("id"),
            total_budget=Sum("allocated_amount"),
        )
    )
    labels = dict(ProjectCategory.choices)
    peak = max((row["total_budget"] or Decimal("0")) for row in raw) if raw else Decimal("0")
    rows = []
    for row in raw:
        budget = row["total_budget"] or Decimal("0")
        rows.append(
            {
                "category": row["category"],
                "label": labels.get(row["category"], row["category"]),
                "project_count": row["project_count"] or 0,
                "total_budget": budget,
                "formatted_budget": format_budget(budget),
                "budget_width": _bar_width(budget, peak),
            }
        )
    rows.sort(key=lambda item: (-item["total_budget"], item["label"]))
    return rows


def year_chart_rows(county=""):
    qs = Project.objects.exclude(financial_year="")
    if county:
        qs = qs.filter(county__iexact=county)
    raw = list(
        qs.values("financial_year").annotate(
            project_count=Count("id"),
            total_budget=Sum("allocated_amount"),
        )
    )
    peak = max((row["total_budget"] or Decimal("0")) for row in raw) if raw else Decimal("0")
    rows = []
    for row in raw:
        budget = row["total_budget"] or Decimal("0")
        rows.append(
            {
                "year": row["financial_year"],
                "label": row["financial_year"],
                "project_count": row["project_count"] or 0,
                "total_budget": budget,
                "formatted_budget": format_budget(budget),
                "budget_width": _bar_width(budget, peak),
            }
        )
    rows.sort(key=lambda item: item["year"] or "")
    return rows


def allocation_total(county=""):
    qs = BudgetAllocation.objects.all()
    if county:
        qs = qs.filter(project__county__iexact=county)
    amount = qs.aggregate(total=Sum("amount"))["total"]
    return format_budget(amount)


def county_coverage(county):
    projects = list(
        Project.objects.filter(county__iexact=county).prefetch_related("evidence_items")
    )
    if not projects:
        return {"percent": 0, "project_count": 0}
    percents = [calculate_evidence_coverage(project)["percent"] for project in projects]
    return {
        "percent": round(sum(percents) / len(percents)),
        "project_count": len(projects),
    }


def county_status_mix(row):
    if not row:
        return {"stops": "", "items": []}
    items = [
        ("completed", "Completed", row["completed_width"], "var(--verified)"),
        ("in-progress", "In progress", row["progress_width"], "var(--link)"),
        ("delayed", "Delayed", row["delayed_width"], "var(--danger)"),
        ("other", "Other / unknown", row["other_width"], "var(--unknown)"),
    ]
    cursor = 0
    stops = []
    for _key, _label, width, color in items:
        nxt = cursor + width
        stops.append(f"{color} {cursor}% {nxt}%")
        cursor = nxt
    return {"stops": ", ".join(stops) if stops else "var(--paper) 0 100%", "items": items}


def county_snapshot(county):
    county = (county or "").strip()
    if not county:
        return None
    rankings = {row["county"]: row for row in decorate_county_charts(county_rankings())}
    row = rankings.get(county)
    if not row:
        match = next((name for name in rankings if name.lower() == county.lower()), None)
        row = rankings.get(match) if match else None
        county = match or county
    if not row:
        return None
    return {
        "county": county,
        "row": row,
        "mix": county_status_mix(row),
        "categories": category_chart_rows(county),
        "years": year_chart_rows(county),
        "allocation_total": allocation_total(county),
        "coverage": county_coverage(county),
    }
