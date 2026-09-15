from django.urls import path

from apps.staff import views

app_name = "staff"

urlpatterns = [
    path("", views.StaffDashboardView.as_view(), name="dashboard"),
    path("projects/", views.ProjectListView.as_view(), name="projects"),
    path("projects/new/", views.ProjectCreateView.as_view(), name="project-create"),
    path("projects/<uuid:pk>/", views.ProjectUpdateView.as_view(), name="project-edit"),
    path("projects/<uuid:pk>/delete/", views.ProjectDeleteView.as_view(), name="project-delete"),
    path("institutions/", views.InstitutionListView.as_view(), name="institutions"),
    path("institutions/new/", views.InstitutionCreateView.as_view(), name="institution-create"),
    path("institutions/<uuid:pk>/", views.InstitutionUpdateView.as_view(), name="institution-edit"),
    path("institutions/<uuid:pk>/delete/", views.InstitutionDeleteView.as_view(), name="institution-delete"),
    path("documents/", views.DocumentListView.as_view(), name="documents"),
    path("documents/new/", views.DocumentCreateView.as_view(), name="document-create"),
    path("documents/<uuid:pk>/", views.DocumentUpdateView.as_view(), name="document-edit"),
    path("documents/<uuid:pk>/delete/", views.DocumentDeleteView.as_view(), name="document-delete"),
    path("evidence/", views.EvidenceListView.as_view(), name="evidence"),
    path("evidence/new/", views.EvidenceCreateView.as_view(), name="evidence-create"),
    path("evidence/<uuid:pk>/", views.EvidenceUpdateView.as_view(), name="evidence-edit"),
    path("evidence/<uuid:pk>/delete/", views.EvidenceDeleteView.as_view(), name="evidence-delete"),
    path("policies/", views.PolicyListView.as_view(), name="policies"),
    path("policies/new/", views.PolicyCreateView.as_view(), name="policy-create"),
    path("policies/<uuid:pk>/", views.PolicyUpdateView.as_view(), name="policy-edit"),
    path("policies/<uuid:pk>/delete/", views.PolicyDeleteView.as_view(), name="policy-delete"),
    path("investigations/", views.InvestigationListView.as_view(), name="investigations"),
    path("investigations/<uuid:pk>/", views.InvestigationUpdateView.as_view(), name="investigation-edit"),
    path("investigations/<uuid:pk>/delete/", views.InvestigationDeleteView.as_view(), name="investigation-delete"),
    path("reports/", views.ReportListView.as_view(), name="reports"),
    path("reports/<uuid:pk>/", views.ReportUpdateView.as_view(), name="report-edit"),
    path("reports/<uuid:pk>/delete/", views.ReportDeleteView.as_view(), name="report-delete"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/<uuid:pk>/", views.UserUpdateView.as_view(), name="user-edit"),
]
