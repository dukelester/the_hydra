from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from apps.core.forms import InvestigationForm
from apps.core.permissions import (
    SESSION_INVESTIGATIONS,
    can_view_investigation,
    remember_id,
)
from apps.investigations.models import Investigation
from apps.projects.models import Project


class MyInvestigationsView(ListView):
    template_name = "investigations/list.html"
    context_object_name = "investigations"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Investigation.objects.select_related("project")
            return Investigation.objects.select_related("project").filter(user=user)
        ids = self.request.session.get(SESSION_INVESTIGATIONS, [])
        return Investigation.objects.select_related("project").filter(pk__in=ids)


def investigate_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    form = InvestigationForm(request.POST or None, request.FILES or None, project=project)
    if request.method == "POST" and form.is_valid():
        investigation = form.save(commit=False)
        investigation.project = project
        if request.user.is_authenticated:
            investigation.user = request.user
            investigation.is_anonymous = False
        else:
            investigation.user = None
            investigation.is_anonymous = True
        investigation.save()
        remember_id(request, SESSION_INVESTIGATIONS, investigation.pk)
        messages.success(
            request,
            "Observation submitted. It is recorded as a citizen observation, not as verified fact.",
        )
        return redirect(investigation.get_absolute_url())
    return render(
        request,
        "investigations/form.html",
        {
            "form": form,
            "project": project,
            "max_upload_mb": settings.THEHYDRA_MAX_UPLOAD_BYTES // (1024 * 1024),
        },
    )


def investigation_detail(request, pk):
    investigation = get_object_or_404(
        Investigation.objects.select_related("project", "user"),
        pk=pk,
    )
    if not can_view_investigation(request, investigation):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        raise Http404("Investigation not found.")
    return render(
        request,
        "investigations/detail.html",
        {"investigation": investigation, "project": investigation.project},
    )
