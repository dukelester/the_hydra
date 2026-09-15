from django.urls import path

from apps.investigations.api_views import InvestigationDetailAPIView, InvestigationCreateAPIView
from apps.policies.api_views import PolicyListAPIView
from apps.projects.api_views import (
    InstitutionListAPIView,
    ProjectDetailAPIView,
    ProjectEvidenceAPIView,
    ProjectListAPIView,
    ProjectTimelineAPIView,
)
from apps.core.api_views import SearchAPIView
from apps.reports.api_views import ReportCreateAPIView, ReportDetailAPIView

urlpatterns = [
    path("projects/", ProjectListAPIView.as_view(), name="api-project-list"),
    path("projects/<uuid:pk>/", ProjectDetailAPIView.as_view(), name="api-project-detail"),
    path(
        "projects/<uuid:pk>/evidence/",
        ProjectEvidenceAPIView.as_view(),
        name="api-project-evidence",
    ),
    path(
        "projects/<uuid:pk>/timeline/",
        ProjectTimelineAPIView.as_view(),
        name="api-project-timeline",
    ),
    path("institutions/", InstitutionListAPIView.as_view(), name="api-institution-list"),
    path("policies/", PolicyListAPIView.as_view(), name="api-policy-list"),
    path("search/", SearchAPIView.as_view(), name="api-search"),
    path("investigations/", InvestigationCreateAPIView.as_view(), name="api-investigation-create"),
    path(
        "investigations/<uuid:pk>/",
        InvestigationDetailAPIView.as_view(),
        name="api-investigation-detail",
    ),
    path("reports/", ReportCreateAPIView.as_view(), name="api-report-create"),
    path("reports/<uuid:pk>/", ReportDetailAPIView.as_view(), name="api-report-detail"),
]
