from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.MyReportsView.as_view(), name="list"),
    path("generate/<int:investigation_id>/", views.generate_report, name="generate"),
    path("<int:pk>/", views.report_detail, name="detail"),
]
