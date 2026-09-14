from django.urls import path

from apps.projects import views

app_name = "institutions"

urlpatterns = [
    path("", views.InstitutionListView.as_view(), name="list"),
    path("<slug:slug>/", views.InstitutionDetailView.as_view(), name="detail"),
]
