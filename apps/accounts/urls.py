from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.TheHydraLoginView.as_view(), name="login"),
    path("logout/", views.TheHydraLogoutView.as_view(), name="logout"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
]
