from django.urls import path

from apps.investigations.views import investigate_project

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("compare/", views.compare_view, name="compare"),
    path("compare/clear/", views.compare_clear_view, name="compare-clear"),
    path("compare/<slug:slug>/add/", views.compare_add_view, name="compare-add"),
    path("compare/<slug:slug>/remove/", views.compare_remove_view, name="compare-remove"),
    path("<slug:slug>/track/", views.toggle_track_view, name="toggle-track"),
    path("<slug:slug>/favourite/", views.toggle_favourite_view, name="toggle-favourite"),
    path("<slug:slug>/investigate/", investigate_project, name="investigate"),
    path("<slug:slug>/", views.ProjectDetailView.as_view(), name="detail"),
]
