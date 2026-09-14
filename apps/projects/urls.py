from django.urls import path

from apps.investigations.views import investigate_project

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("<slug:slug>/investigate/", investigate_project, name="investigate"),
    path("<slug:slug>/", views.ProjectDetailView.as_view(), name="detail"),
]
