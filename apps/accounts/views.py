from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from apps.core.forms import LoginForm, ProfileForm, RegisterForm


class TheHydraLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class TheHydraLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("accounts:dashboard")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard_view(request):
    investigations = request.user.investigations.select_related("project")
    reports = request.user.reports.select_related("project")
    return render(
        request,
        "accounts/dashboard.html",
        {
            "investigation_count": investigations.count(),
            "report_count": reports.count(),
            "recent_investigations": investigations[:5],
            "recent_reports": reports[:5],
        },
    )


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile saved.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})
