from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.TheHydraLoginView.as_view(), name="login"),
    path("logout/", views.TheHydraLogoutView.as_view(), name="logout"),
    path("register/", views.register_view, name="register"),
    path("password-reset/", views.TheHydraPasswordResetView.as_view(), name="password-reset"),
    path(
        "password-reset/done/",
        views.TheHydraPasswordResetDoneView.as_view(),
        name="password-reset-done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        views.TheHydraPasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "password-reset/complete/",
        views.TheHydraPasswordResetCompleteView.as_view(),
        name="password-reset-complete",
    ),
    path("password-change/", views.TheHydraPasswordChangeView.as_view(), name="password-change"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
]
