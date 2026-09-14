import json
from copy import deepcopy
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from django.db.models import Q

from apps.core.services.coverage import calculate_evidence_coverage
from apps.projects.models import Project, ProjectStatus

_AREA_DATA = Path(__file__).resolve().parent / "data" / "kenya_areas.json"

COUNTY_ALIASES = {
    "Taita/Taveta": "Taita-Taveta",
    "Taita Taveta": "Taita-Taveta",
    "Elgeyo/Marakwet": "Elgeyo-Marakwet",
    "Elgeyo Marakwet": "Elgeyo-Marakwet",
    "Nairobi City": "Nairobi",
    "Tharaka - Nithi": "Tharaka-Nithi",
}


def normalize_area_name(name):
    name = (name or "").replace("\u2019", "'").replace("\u2018", "'").strip()
    return COUNTY_ALIASES.get(name, name)


@lru_cache(maxsize=1)
def official_area_tree():
    return json.loads(_AREA_DATA.read_text(encoding="utf-8"))


def area_tree():
    tree = deepcopy(official_area_tree())
    rows = (
        Project.objects.exclude(county="")
        .values_list("county", "constituency", "ward")
        .distinct()
    )
    for county_name, constituency, ward in rows:
        county_name = normalize_area_name(county_name)
        constituency = normalize_area_name(constituency)
        ward = normalize_area_name(ward)
        if not county_name:
            continue
        tree.setdefault(county_name, {})
        if constituency:
            wards = tree[county_name].setdefault(constituency, [])
            if ward and ward not in wards:
                wards.append(ward)
                wards.sort()
    return dict(sorted((county, dict(sorted(branches.items()))) for county, branches in tree.items()))


def area_counties():
    return list(area_tree().keys())


def constituencies_for(county):
    county = normalize_area_name(county)
    if not county:
        return []
    return list(area_tree().get(county, {}).keys())


def wards_for(county, constituency):
    county = normalize_area_name(county)
    constituency = normalize_area_name(constituency)
    if not county or not constituency:
        return []
    return list(area_tree().get(county, {}).get(constituency, []))


def is_valid_area(county, constituency="", ward=""):
    county = normalize_area_name(county)
    constituency = normalize_area_name(constituency)
    ward = normalize_area_name(ward)
    if not county or county not in area_tree():
        return False
    if constituency and constituency not in area_tree()[county]:
        return False
    if ward and (not constituency or ward not in area_tree()[county].get(constituency, [])):
        return False
    return True


KENYA_COUNTIES = tuple(official_area_tree().keys())


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


def area_projects_for_watches(watches):
    qs = Project.objects.none()
    for watch in watches:
        qs = qs | area_project_queryset(watch.county, watch.constituency, watch.ward)
    return qs.distinct().select_related("institution").prefetch_related("evidence_items").order_by(
        "-updated_at", "name"
    )


def _watch_matches_project(watch, project):
    if (project.county or "").lower() != (watch.county or "").lower():
        return False
    constituency = (watch.constituency or "").strip().lower()
    ward = (watch.ward or "").strip().lower()
    if constituency:
        haystack = " ".join(
            part for part in (project.constituency, project.ward, project.location) if part
        ).lower()
        if constituency not in haystack:
            return False
    if ward:
        haystack = " ".join(part for part in (project.ward, project.location) if part).lower()
        if ward not in haystack:
            return False
    return True


def area_watch_context(user, mark_seen=False):
    from django.utils import timezone

    empty = {
        "watching": False,
        "watches": [],
        "watch_count": 0,
        "can_add": True,
        "max_watches": 4,
        "projects": [],
        "area_updates": [],
        "area_update_count": 0,
        "area_count": 0,
        "status_totals": [],
        "total_budget": "Information unavailable",
        "label": "",
    }
    if not user.is_authenticated:
        return empty

    watches = list(user.area_watches.all())
    if not watches:
        empty["max_watches"] = user.area_watches.model.MAX_PER_USER
        return empty

    projects = list(area_projects_for_watches(watches))
    updates = []
    for project in projects:
        project.coverage = calculate_evidence_coverage(project)
        project.is_new_in_area = False
        for watch in watches:
            if (
                watch.last_seen_at
                and project.updated_at > watch.last_seen_at
                and _watch_matches_project(watch, project)
            ):
                project.is_new_in_area = True
                break
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
        now = timezone.now()
        user.area_watches.update(last_seen_at=now)
        user.area_last_seen_at = now
        user.save(update_fields=["area_last_seen_at"])

    max_watches = user.area_watches.model.MAX_PER_USER
    return {
        "watching": True,
        "watches": watches,
        "watch_count": len(watches),
        "can_add": len(watches) < max_watches,
        "max_watches": max_watches,
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
    return area_counties()


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
