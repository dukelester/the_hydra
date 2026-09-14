from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.forms import (
    AreaWatchForm,
    LoginForm,
    ProfileForm,
    RegisterForm,
    RegisterIdentityForm,
    StyledPasswordChangeForm,
    StyledPasswordResetForm,
    StyledSetPasswordForm,
)
from apps.core.services.coverage import calculate_evidence_coverage
from apps.projects.activity import favourite_projects, recent_projects_for, tracked_follows
from apps.projects.area import (
    area_watch_context,
    constituencies_for,
    wards_for,
)


class TheHydraLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class TheHydraLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


REGISTER_DRAFT_KEY = "register_draft"


def _register_context(step, form, draft=None):
    return {
        "step": step,
        "form": form,
        "draft": draft or {},
    }


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    draft = request.session.get(REGISTER_DRAFT_KEY) or {}

    if request.method == "POST":
        posted_step = request.POST.get("step", "1")
        if request.POST.get("intent") == "back" or posted_step == "back":
            form = RegisterIdentityForm(initial=draft)
            return render(request, "accounts/register.html", _register_context(1, form, draft))

        if posted_step == "1":
            form = RegisterIdentityForm(request.POST)
            if form.is_valid():
                request.session[REGISTER_DRAFT_KEY] = {
                    "username": form.cleaned_data["username"],
                    "display_name": form.cleaned_data.get("display_name") or "",
                }
                draft = request.session[REGISTER_DRAFT_KEY]
                security = RegisterForm(initial=draft)
                return render(request, "accounts/register.html", _register_context(2, security, draft))
            return render(request, "accounts/register.html", _register_context(1, form, draft))

        if not draft.get("username"):
            form = RegisterIdentityForm()
            return render(request, "accounts/register.html", _register_context(1, form))

        data = request.POST.copy()
        data["username"] = draft["username"]
        data["display_name"] = draft.get("display_name", "")
        form = RegisterForm(data)
        if form.is_valid():
            user = form.save()
            request.session.pop(REGISTER_DRAFT_KEY, None)
            login(request, user)
            return redirect("accounts:dashboard")
        return render(request, "accounts/register.html", _register_context(2, form, draft))

    if request.GET.get("step") == "2" and draft.get("username"):
        form = RegisterForm(initial=draft)
        return render(request, "accounts/register.html", _register_context(2, form, draft))

    form = RegisterIdentityForm(initial=draft or None)
    return render(request, "accounts/register.html", _register_context(1, form, draft))


@login_required
def dashboard_view(request):
    investigations = request.user.investigations.select_related("project")
    reports = request.user.reports.select_related("project")
    follows = tracked_follows(request.user)
    favourites = favourite_projects(request.user)
    recent_projects = recent_projects_for(request)
    for project in recent_projects + favourites + [follow.project for follow in follows]:
        project.coverage = calculate_evidence_coverage(project)
    updates = [follow for follow in follows if follow.needs_attention]
    area = area_watch_context(request.user)
    return render(
        request,
        "accounts/dashboard.html",
        {
            "investigation_count": investigations.count(),
            "report_count": reports.count(),
            "recent_investigations": investigations[:5],
            "recent_reports": reports[:5],
            "recent_projects": recent_projects,
            "tracked_follows": follows,
            "favourite_projects": favourites,
            "tracked_updates": updates,
            "tracked_count": len(follows),
            "favourite_count": len(favourites),
            "update_count": len(updates),
            "area": area,
        },
    )


@login_required
def profile_view(request):
    form = ProfileForm(request.POST if request.method == "POST" else None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile saved.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def my_county_view(request):
    user = request.user

    if request.method == "POST" and request.POST.get("intent") == "stop":
        user.area_watches.all().delete()
        user.sync_area_tracking()
        messages.success(request, "Stopped tracking all areas. Location details are still on your profile.")
        return redirect("accounts:my-county")

    if request.method == "POST" and request.POST.get("remove"):
        removed = user.area_watches.filter(pk=request.POST.get("remove")).first()
        if removed:
            label = removed.label()
            removed.delete()
            user.sync_area_tracking()
            messages.success(request, f"Stopped tracking {label}.")
        return redirect("accounts:my-county")

    adding = request.method == "POST" and request.POST.get("intent") not in {"stop", "remove"}
    form = AreaWatchForm(request.POST if adding else None, user=user)
    if adding and form.is_valid():
        watch = form.save()
        messages.success(request, f"Tracking {watch.label()}. You can follow up to {watch.MAX_PER_USER} areas.")
        return redirect("accounts:my-county")

    area = area_watch_context(user, mark_seen=user.is_watching_area())
    return render(
        request,
        "accounts/my_county.html",
        {
            "form": form,
            "area": area,
        },
    )


@login_required
@require_GET
def area_options_view(request):
    trigger = request.headers.get("HX-Trigger-Name", "")
    county = (request.GET.get("county") or "").strip()
    constituency = (request.GET.get("constituency") or "").strip()
    if trigger == "county":
        constituency = ""
    context = {
        "county": county,
        "constituency": constituency,
        "constituencies": constituencies_for(county),
        "wards": wards_for(county, constituency),
        "selected_constituency": constituency,
        "selected_ward": "",
    }
    if trigger == "constituency":
        return render(request, "accounts/_area_ward_field.html", context)
    return render(request, "accounts/_area_dependent_fields.html", context)


class TheHydraPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/email/password_reset_email.txt"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    form_class = StyledPasswordResetForm
    success_url = reverse_lazy("accounts:password-reset-done")


class TheHydraPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class TheHydraPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = StyledSetPasswordForm
    success_url = reverse_lazy("accounts:password-reset-complete")


class TheHydraPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class TheHydraPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Password updated.")
        return super().form_valid(form)
