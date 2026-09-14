from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from apps.core.services.coverage import calculate_evidence_coverage
from apps.core.services.search import project_search_queryset
from apps.core.services.timeline import build_project_timeline
from apps.projects.activity import (
    MAX_COMPARE,
    add_to_compare,
    attach_coverage,
    clear_compare,
    compare_slugs,
    follow_for,
    record_project_view,
    remove_from_compare,
    toggle_favourite,
    toggle_tracked,
)
from apps.projects.compare import (
    county_compare_rows,
    county_rankings,
    ranking_highlights,
    status_totals,
)
from apps.projects.models import Institution, Project
from apps.sources.models import Evidence


def _safe_next(request, fallback):
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
        return candidate
    return fallback


class ProjectListView(ListView):
    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        county = self.request.GET.get("county")
        status = self.request.GET.get("status")
        category = self.request.GET.get("category")
        q = self.request.GET.get("q")
        if q:
            qs = project_search_queryset(
                q, county=county or "", status=status or "", category=category or ""
            )
        else:
            qs = Project.objects.select_related("institution")
            if county:
                qs = qs.filter(county__iexact=county)
            if status:
                qs = qs.filter(status=status)
            if category:
                qs = qs.filter(category=category)
            qs = qs.order_by("name")
        return qs.prefetch_related("evidence_items").annotate(evidence_count=Count("evidence_items"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for project in context["projects"]:
            project.coverage = calculate_evidence_coverage(project)
        counties = (
            Project.objects.order_by("county").values_list("county", flat=True).distinct()
        )
        context.update(
            {
                "counties": counties,
                "selected_county": self.request.GET.get("county", ""),
                "selected_status": self.request.GET.get("status", ""),
                "selected_category": self.request.GET.get("category", ""),
            }
        )
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = "projects/detail.html"
    context_object_name = "project"
    slug_field = "slug"

    def get_queryset(self):
        return Project.objects.select_related("institution").prefetch_related(
            "allocations__source_document",
            "source_documents",
            Prefetch(
                "evidence_items",
                queryset=Evidence.objects.select_related("source_document"),
            ),
            "timeline_events__evidence__source_document",
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_project_view(request, self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        follow = follow_for(self.request.user, project)
        context["timeline"] = build_project_timeline(project)
        context["coverage"] = calculate_evidence_coverage(project)
        context["allocations"] = project.allocations.all()
        context["evidence_items"] = project.evidence_items.all()
        context["documents"] = project.source_documents.all()
        context["is_tracked"] = bool(follow and follow.is_tracked)
        context["is_favourite"] = bool(follow and follow.is_favourite)
        context["in_compare"] = project.slug in compare_slugs(self.request)
        return context


class InstitutionListView(ListView):
    model = Institution
    template_name = "institutions/list.html"
    context_object_name = "institutions"
    paginate_by = 9

    def get_queryset(self):
        return Institution.objects.annotate(project_count=Count("projects")).order_by("name")


class InstitutionDetailView(DetailView):
    model = Institution
    template_name = "institutions/detail.html"
    context_object_name = "institution"
    slug_field = "slug"

    def get_queryset(self):
        return Institution.objects.prefetch_related(
            Prefetch(
                "projects",
                queryset=Project.objects.select_related("institution").prefetch_related(
                    "evidence_items"
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = list(self.object.projects.all())
        for project in projects:
            project.coverage = calculate_evidence_coverage(project)
        context["projects"] = projects
        return context


def project_card_partial(request, slug):
    project = get_object_or_404(Project.objects.select_related("institution"), slug=slug)
    project.coverage = calculate_evidence_coverage(project)
    return render(request, "components/project_card.html", {"project": project})


@login_required
@require_POST
def toggle_track_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    follow = toggle_tracked(request.user, project)
    if follow and follow.is_tracked:
        messages.success(request, f"Tracking {project.name}. Dashboard will show status changes.")
    else:
        messages.success(request, f"Stopped tracking {project.name}.")
    return redirect(_safe_next(request, project.get_absolute_url()))


@login_required
@require_POST
def toggle_favourite_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    follow = toggle_favourite(request.user, project)
    if follow and follow.is_favourite:
        messages.success(request, f"{project.name} saved to favourites.")
    else:
        messages.success(request, f"Removed {project.name} from favourites.")
    return redirect(_safe_next(request, project.get_absolute_url()))


@require_POST
def compare_add_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    slugs = add_to_compare(request, project)
    messages.success(request, f"Added to compare ({len(slugs)} of {MAX_COMPARE}).")
    return redirect(_safe_next(request, "projects:compare"))


@require_POST
def compare_remove_view(request, slug):
    remove_from_compare(request, slug)
    messages.success(request, "Removed from compare.")
    return redirect(_safe_next(request, "projects:compare"))


@require_POST
def compare_clear_view(request):
    clear_compare(request)
    messages.success(request, "Compare list cleared.")
    return redirect("projects:compare")


def compare_view(request):
    if request.GET.get("reset"):
        clear_compare(request)
        selected_slugs = []
        selected_counties = []
    else:
        selected_slugs = [slug for slug in request.GET.getlist("p") if slug]
        if selected_slugs:
            request.session["compare_project_slugs"] = selected_slugs[:MAX_COMPARE]
            selected_slugs = selected_slugs[:MAX_COMPARE]
        else:
            selected_slugs = compare_slugs(request)
        selected_counties = [name for name in request.GET.getlist("county") if name]
    projects = list(
        Project.objects.select_related("institution")
        .prefetch_related("evidence_items")
        .filter(slug__in=selected_slugs)
    )
    by_slug = {project.slug: project for project in projects}
    projects = [by_slug[slug] for slug in selected_slugs if slug in by_slug]
    attach_coverage(projects)

    rankings = county_rankings()
    return render(
        request,
        "projects/compare.html",
        {
            "projects": projects,
            "selected_slugs": selected_slugs,
            "selected_counties": selected_counties,
            "county_rows": county_compare_rows(selected_counties),
            "rankings": rankings,
            "highlights": ranking_highlights(rankings),
            "status_totals": status_totals(),
            "all_projects": Project.objects.select_related("institution").order_by("name"),
            "all_counties": (
                Project.objects.order_by("county").values_list("county", flat=True).distinct()
            ),
            "max_compare": MAX_COMPARE,
        },
    )
