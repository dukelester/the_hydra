from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView

from apps.core.services.coverage import calculate_evidence_coverage
from apps.core.services.search import project_search_queryset
from apps.core.services.timeline import build_project_timeline
from apps.projects.models import Institution, Project
from apps.sources.models import Evidence


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        context["timeline"] = build_project_timeline(project)
        context["coverage"] = calculate_evidence_coverage(project)
        context["allocations"] = project.allocations.all()
        context["evidence_items"] = project.evidence_items.all()
        context["documents"] = project.source_documents.all()
        return context


class InstitutionListView(ListView):
    model = Institution
    template_name = "institutions/list.html"
    context_object_name = "institutions"
    paginate_by = 20

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
