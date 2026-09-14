from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.core.services.coverage import calculate_evidence_coverage
from apps.core.services.search import search_civic_data
from apps.investigations.models import Investigation
from apps.projects.models import Project


class HomeView(TemplateView):
    template_name = "home/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured = list(
            Project.objects.select_related("institution")
            .filter(is_featured=True)
            .prefetch_related("evidence_items")[:6]
        )
        if len(featured) < 3:
            extra = (
                Project.objects.select_related("institution")
                .prefetch_related("evidence_items")
                .exclude(pk__in=[p.pk for p in featured])[: 6 - len(featured)]
            )
            featured.extend(extra)
        for project in featured:
            project.coverage = calculate_evidence_coverage(project)
        recent = (
            Investigation.objects.select_related("project")
            .order_by("-created_at")[:5]
        )
        context.update(
            {
                "featured_projects": featured,
                "recent_investigations": recent,
            }
        )
        return context


class HowItWorksView(TemplateView):
    template_name = "home/how_it_works.html"


def search_view(request):
    query = request.GET.get("q", "")
    results = search_civic_data(query, limit=8)
    template = (
        "components/search_results.html"
        if request.headers.get("HX-Request")
        else "home/search.html"
    )
    return render(request, template, results)


@login_required
def account_home(request):
    return render(request, "accounts/home.html")
