from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.MyReportsView.as_view(), name="list"),
    path("counties/", views.county_report_view, name="counties"),
    path("generate/<uuid:investigation_id>/", views.generate_report, name="generate"),
    path("<uuid:pk>/", views.report_detail, name="detail"),
]
