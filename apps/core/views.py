from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.core.services.coverage import calculate_evidence_coverage
from apps.core.services.search import (
    document_search_queryset,
    project_search_queryset,
    search_civic_data,
)
from apps.investigations.models import Investigation
from apps.projects.models import Project, ProjectCategory, ProjectStatus


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


class WhatHydraMeansView(TemplateView):
    template_name = "home/what_hydra_means.html"


def search_suggest(request):
    results = search_civic_data(
        request.GET.get("q", ""),
        limit=7,
        suggest=True,
        kind=request.GET.get("kind", "all"),
        county=request.GET.get("county", ""),
        status=request.GET.get("status", ""),
        category=request.GET.get("category", ""),
    )
    return render(request, "components/search_suggest.html", results)


def _nonempty_params(**values):
    return {key: value for key, value in values.items() if value}


def search_view(request):
    query = request.GET.get("q", "")
    kind = request.GET.get("kind", "all") or "all"
    county = request.GET.get("county", "")
    status = request.GET.get("status", "")
    category = request.GET.get("category", "")
    if request.headers.get("HX-Request") and request.GET.get("live"):
        return search_suggest(request)

    results = search_civic_data(
        query,
        limit=8,
        suggest=False,
        kind=kind,
        county=county,
        status=status,
        category=category,
    )
    project_page = None
    document_page = None
    if kind in {"all", "projects"} and query:
        paginator = Paginator(
            project_search_queryset(query, county=county, status=status, category=category),
            20,
        )
        project_page = paginator.get_page(request.GET.get("page") or 1)
        if kind == "projects":
            results["projects"] = list(project_page.object_list)
    if kind == "documents" and query:
        paginator = Paginator(document_search_queryset(query), 20)
        document_page = paginator.get_page(request.GET.get("page") or 1)
        results["documents"] = list(document_page.object_list)
        for document in results["documents"]:
            document.search_snippet = document.snippet_for(results["query"])

    tab_params = _nonempty_params(q=query, county=county, status=status, category=category)
    page_params = dict(tab_params)
    if kind and kind != "all":
        page_params["kind"] = kind
    counties = Project.objects.order_by("county").values_list("county", flat=True).distinct()
    results.update(
        {
            "project_page": project_page,
            "document_page": document_page,
            "counties": counties,
            "status_choices": ProjectStatus.choices,
            "category_choices": ProjectCategory.choices,
            "tab_querystring": urlencode(tab_params),
            "page_querystring": urlencode(page_params),
        }
    )
    template = (
        "components/search_results.html"
        if request.headers.get("HX-Request")
        else "home/search.html"
    )
    return render(request, template, results)


@login_required
def account_home(request):
    return render(request, "accounts/home.html")
