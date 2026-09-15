from django.urls import path

from apps.staff import views

app_name = "staff"

urlpatterns = [
    path("", views.StaffDashboardView.as_view(), name="dashboard"),
    path("projects/", views.ProjectListView.as_view(), name="projects"),
    path("projects/new/", views.ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/", views.ProjectUpdateView.as_view(), name="project-edit"),
    path("projects/<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="project-delete"),
    path("institutions/", views.InstitutionListView.as_view(), name="institutions"),
    path("institutions/new/", views.InstitutionCreateView.as_view(), name="institution-create"),
    path("institutions/<int:pk>/", views.InstitutionUpdateView.as_view(), name="institution-edit"),
    path("institutions/<int:pk>/delete/", views.InstitutionDeleteView.as_view(), name="institution-delete"),
    path("documents/", views.DocumentListView.as_view(), name="documents"),
    path("documents/new/", views.DocumentCreateView.as_view(), name="document-create"),
    path("documents/<int:pk>/", views.DocumentUpdateView.as_view(), name="document-edit"),
    path("documents/<int:pk>/delete/", views.DocumentDeleteView.as_view(), name="document-delete"),
    path("evidence/", views.EvidenceListView.as_view(), name="evidence"),
    path("evidence/new/", views.EvidenceCreateView.as_view(), name="evidence-create"),
    path("evidence/<int:pk>/", views.EvidenceUpdateView.as_view(), name="evidence-edit"),
    path("evidence/<int:pk>/delete/", views.EvidenceDeleteView.as_view(), name="evidence-delete"),
    path("policies/", views.PolicyListView.as_view(), name="policies"),
    path("policies/new/", views.PolicyCreateView.as_view(), name="policy-create"),
    path("policies/<int:pk>/", views.PolicyUpdateView.as_view(), name="policy-edit"),
    path("policies/<int:pk>/delete/", views.PolicyDeleteView.as_view(), name="policy-delete"),
    path("investigations/", views.InvestigationListView.as_view(), name="investigations"),
    path("investigations/<int:pk>/", views.InvestigationUpdateView.as_view(), name="investigation-edit"),
    path("investigations/<int:pk>/delete/", views.InvestigationDeleteView.as_view(), name="investigation-delete"),
    path("reports/", views.ReportListView.as_view(), name="reports"),
    path("reports/<int:pk>/", views.ReportUpdateView.as_view(), name="report-edit"),
    path("reports/<int:pk>/delete/", views.ReportDeleteView.as_view(), name="report-delete"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/<int:pk>/", views.UserUpdateView.as_view(), name="user-edit"),
]
