from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from apps.core.governance import request_country
from apps.core.forms import ReportReviewForm
from apps.core.permissions import (
    SESSION_REPORTS,
    can_create_report_for_investigation,
    can_view_report,
    remember_id,
)
from apps.investigations.models import Investigation
from apps.projects.compare import county_rankings, ranking_highlights
from apps.reports.analytics import (
    category_chart_rows,
    county_snapshot,
    decorate_county_charts,
    year_chart_rows,
)
from apps.reports.models import IssueReport
from apps.reports.services import generate_report_from_investigation


class MyReportsView(ListView):
    template_name = "reports/list.html"
    context_object_name = "reports"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return IssueReport.objects.select_related("project", "investigation")
            return IssueReport.objects.select_related("project").filter(user=user)
        ids = self.request.session.get(SESSION_REPORTS, [])
        return IssueReport.objects.select_related("project").filter(pk__in=ids)


def generate_report(request, investigation_id):
    investigation = get_object_or_404(
        Investigation.objects.select_related("project"),
        pk=investigation_id,
    )
    if not can_create_report_for_investigation(request, investigation):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        raise Http404("Investigation not found.")

    existing = investigation.reports.order_by("-created_at").first()
    if request.method != "POST" and existing:
        return redirect(existing.get_absolute_url())

    if request.method == "POST":
        user = request.user if request.user.is_authenticated else None
        report = generate_report_from_investigation(investigation, user=user)
        remember_id(request, SESSION_REPORTS, report.pk)
        messages.success(
            request,
            "A structured accountability report was generated from the investigation. Review it before saving.",
        )
        return redirect(report.get_absolute_url())

    return render(
        request,
        "reports/generate.html",
        {"investigation": investigation, "project": investigation.project},
    )


def report_detail(request, pk):
    report = get_object_or_404(
        IssueReport.objects.select_related("project", "investigation", "user"),
        pk=pk,
    )
    if not can_view_report(request, report):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        raise Http404("Report not found.")

    form = ReportReviewForm(request.POST or None, instance=report)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, "Report saved. It remains private unless an administrator publishes it.")
        return redirect(saved.get_absolute_url())

    sources = report.project.source_documents.all()
    return render(
        request,
        "reports/detail.html",
        {
            "report": report,
            "project": report.project,
            "investigation": report.investigation,
            "form": form,
            "sources": sources,
            "county_view": county_snapshot(report.project.county, country=report.project.country),
        },
    )


def county_report_view(request):
    country = request_country(request)
    rankings = decorate_county_charts(county_rankings(country))
    names = [row["county"] for row in rankings]
    selected = (request.GET.get("county") or "").strip()
    if not selected and request.user.is_authenticated:
        selected = (request.user.county or "").strip()
    if selected and selected not in names:
        selected = next((name for name in names if name.lower() == selected.lower()), "")
    snapshot = county_snapshot(selected, country=country) if selected else None
    return render(
        request,
        "reports/counties.html",
        {
            "rankings": rankings,
            "highlights": ranking_highlights(rankings),
            "categories": category_chart_rows(selected, country=country),
            "years": year_chart_rows(selected, country=country),
            "county_view": snapshot,
            "selected_county": selected,
            "counties": names,
        },
    )
