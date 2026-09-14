from decimal import Decimal

from django.db.models import Q

from apps.core.services.coverage import calculate_evidence_coverage
from apps.projects.models import Project, ProjectStatus

KENYA_COUNTIES = (
    "Baringo",
    "Bomet",
    "Bungoma",
    "Busia",
    "Elgeyo-Marakwet",
    "Embu",
    "Garissa",
    "Homa Bay",
    "Isiolo",
    "Kajiado",
    "Kakamega",
    "Kericho",
    "Kiambu",
    "Kilifi",
    "Kirinyaga",
    "Kisii",
    "Kisumu",
    "Kitui",
    "Kwale",
    "Laikipia",
    "Lamu",
    "Machakos",
    "Makueni",
    "Mandera",
    "Marsabit",
    "Meru",
    "Migori",
    "Mombasa",
    "Murang'a",
    "Nairobi",
    "Nakuru",
    "Nandi",
    "Narok",
    "Nyamira",
    "Nyandarua",
    "Nyeri",
    "Samburu",
    "Siaya",
    "Taita-Taveta",
    "Tana River",
    "Tharaka-Nithi",
    "Trans Nzoia",
    "Turkana",
    "Uasin Gishu",
    "Vihiga",
    "Wajir",
    "West Pokot",
)


def area_project_queryset(county, constituency="", ward=""):
    county = (county or "").strip()
    if not county:
        return Project.objects.none()
    qs = (
        Project.objects.select_related("institution")
        .prefetch_related("evidence_items")
        .filter(county__iexact=county)
    )
    constituency = (constituency or "").strip()
    ward = (ward or "").strip()
    if constituency:
        qs = qs.filter(
            Q(constituency__icontains=constituency)
            | Q(ward__icontains=constituency)
            | Q(location__icontains=constituency)
        )
    if ward:
        qs = qs.filter(Q(ward__icontains=ward) | Q(location__icontains=ward))
    return qs.order_by("-updated_at", "name")


def area_watch_context(user, mark_seen=False):
    from django.utils import timezone

    if not user.is_authenticated or not user.is_watching_area():
        return {
            "watching": False,
            "projects": [],
            "area_updates": [],
            "area_update_count": 0,
            "area_count": 0,
            "status_totals": [],
            "total_budget": "Information unavailable",
            "label": "",
        }

    projects = list(area_project_queryset(user.county, user.constituency, user.ward))
    last_seen = user.area_last_seen_at
    updates = []
    for project in projects:
        project.coverage = calculate_evidence_coverage(project)
        project.is_new_in_area = bool(last_seen and project.updated_at > last_seen)
        if project.is_new_in_area:
            updates.append(project)

    counts = {value: 0 for value, _label in ProjectStatus.choices}
    for project in projects:
        counts[project.status] = counts.get(project.status, 0) + 1
    status_totals = [
        {"status": value, "label": label, "count": counts.get(value, 0)}
        for value, label in ProjectStatus.choices
        if counts.get(value, 0)
    ]
    total = sum((project.allocated_amount or Decimal("0")) for project in projects)
    if mark_seen:
        user.area_last_seen_at = timezone.now()
        user.save(update_fields=["area_last_seen_at"])

    return {
        "watching": True,
        "projects": projects,
        "area_updates": updates,
        "area_update_count": len(updates),
        "area_count": len(projects),
        "status_totals": status_totals,
        "total_budget": f"KSh {total:,.0f}" if total else "Information unavailable",
        "label": user.area_label(),
        "in_progress_count": counts.get(ProjectStatus.IN_PROGRESS, 0),
        "delayed_count": counts.get(ProjectStatus.DELAYED, 0),
    }


def known_counties():
    return list(Project.objects.order_by("county").values_list("county", flat=True).distinct())


def trackable_counties():
    recorded = known_counties()
    extra = [name for name in recorded if name and name not in KENYA_COUNTIES]
    return list(KENYA_COUNTIES) + sorted(extra)


def known_constituencies():
    return list(
        Project.objects.exclude(constituency="")
        .order_by("constituency")
        .values_list("constituency", flat=True)
        .distinct()
    )


def known_wards():
    return list(
        Project.objects.exclude(ward="").order_by("ward").values_list("ward", flat=True).distinct()
    )
