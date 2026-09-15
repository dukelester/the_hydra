from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.accounts.models import User
from apps.investigations.models import Investigation, InvestigationVerificationStatus
from apps.policies.models import Policy
from apps.projects.models import Institution, Project
from apps.reports.models import IssueReport, ReportStatus
from apps.sources.models import Evidence, SourceDocument
from apps.staff.forms import (
    StaffDocumentForm,
    StaffEvidenceForm,
    StaffInstitutionForm,
    StaffInvestigationForm,
    StaffPolicyForm,
    StaffProjectForm,
    StaffReportForm,
    StaffUserForm,
)
from apps.staff.mixins import SearchQueryMixin, StaffRequiredMixin


def _staff_home(request):
    pending_investigations = Investigation.objects.select_related("project").filter(
        verification_status__in=[
            InvestigationVerificationStatus.UNVERIFIED,
            InvestigationVerificationStatus.UNDER_REVIEW,
        ]
    )
    pending_reports = IssueReport.objects.select_related("project").filter(
        status__in=[ReportStatus.SUBMITTED, ReportStatus.UNDER_REVIEW]
    )
    return render(
        request,
        "staff/dashboard.html",
        {
            "counts": {
                "projects": Project.objects.count(),
                "institutions": Institution.objects.count(),
                "documents": SourceDocument.objects.count(),
                "evidence": Evidence.objects.count(),
                "investigations": Investigation.objects.count(),
                "reports": IssueReport.objects.count(),
                "policies": Policy.objects.count(),
                "users": User.objects.count(),
                "pending_investigations": pending_investigations.count(),
                "pending_reports": pending_reports.count(),
                "public_reports": IssueReport.objects.filter(is_public=True).count(),
            },
            "pending_investigations": pending_investigations[:8],
            "pending_reports": pending_reports[:8],
            "recent_projects": Project.objects.select_related("institution").order_by("-updated_at")[:6],
        },
    )


class StaffDashboardView(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return _staff_home(request)


class StaffRecordListView(StaffRequiredMixin, SearchQueryMixin, ListView):
    paginate_by = 25
    template_name = "staff/list.html"
    create_url = ""
    heading = ""
    lede = ""
    columns = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": self.heading,
                "lede": self.lede,
                "create_url": self.create_url,
                "columns": self.columns,
                "row_template": self.row_template,
            }
        )
        return context


class ProjectListView(StaffRecordListView):
    model = Project
    queryset = Project.objects.select_related("institution")
    search_fields = ("name", "county", "contractor", "institution__name")
    heading = "Projects"
    lede = "Create and update civic project files. Leave unknown amounts and dates blank."
    create_url = "staff:project-create"
    row_template = "staff/rows/project.html"
    columns = ("Project", "County", "Status", "Updated")


class ProjectCreateView(StaffRequiredMixin, CreateView):
    model = Project
    form_class = StaffProjectForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:projects")

    def form_valid(self, form):
        messages.success(self.request, "Project saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"heading": "New project", "cancel_url": reverse("staff:projects")})
        return context


class ProjectUpdateView(StaffRequiredMixin, UpdateView):
    model = Project
    form_class = StaffProjectForm
    template_name = "staff/form.html"
    context_object_name = "record"

    def get_success_url(self):
        return reverse("staff:project-edit", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Project saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": self.object.name,
                "cancel_url": reverse("staff:projects"),
                "public_url": self.object.get_absolute_url(),
                "delete_url": reverse("staff:project-delete", args=[self.object.pk]),
            }
        )
        return context


class ProjectDeleteView(StaffRequiredMixin, DeleteView):
    model = Project
    template_name = "staff/confirm_delete.html"
    success_url = reverse_lazy("staff:projects")

    def form_valid(self, form):
        messages.success(self.request, "Project removed.")
        return super().form_valid(form)


class InstitutionListView(StaffRecordListView):
    model = Institution
    search_fields = ("name", "location")
    heading = "Institutions"
    lede = "Departments, agencies, and other bodies attached to projects."
    create_url = "staff:institution-create"
    row_template = "staff/rows/institution.html"
    columns = ("Institution", "Type", "Location")


class InstitutionCreateView(StaffRequiredMixin, CreateView):
    model = Institution
    form_class = StaffInstitutionForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:institutions")

    def form_valid(self, form):
        messages.success(self.request, "Institution saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"heading": "New institution", "cancel_url": reverse("staff:institutions")})
        return context


class InstitutionUpdateView(StaffRequiredMixin, UpdateView):
    model = Institution
    form_class = StaffInstitutionForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:institutions")

    def form_valid(self, form):
        messages.success(self.request, "Institution saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": self.object.name,
                "cancel_url": reverse("staff:institutions"),
                "public_url": self.object.get_absolute_url(),
                "delete_url": reverse("staff:institution-delete", args=[self.object.pk]),
            }
        )
        return context


class InstitutionDeleteView(StaffRequiredMixin, DeleteView):
    model = Institution
    template_name = "staff/confirm_delete.html"
    success_url = reverse_lazy("staff:institutions")

    def form_valid(self, form):
        try:
            messages.success(self.request, "Institution removed.")
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "This institution still has projects. Move or remove those projects first.",
            )
            return redirect("staff:institution-edit", pk=self.object.pk)


class DocumentListView(StaffRecordListView):
    model = SourceDocument
    search_fields = ("title", "publisher", "original_filename")
    heading = "Documents"
    lede = "Source files that claims should point to. Text is extracted after save."
    create_url = "staff:document-create"
    row_template = "staff/rows/document.html"
    columns = ("Document", "Publisher", "Verification")


class DocumentCreateView(StaffRequiredMixin, CreateView):
    model = SourceDocument
    form_class = StaffDocumentForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:documents")

    def form_valid(self, form):
        messages.success(self.request, "Document saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"heading": "New document", "cancel_url": reverse("staff:documents")})
        return context


class DocumentUpdateView(StaffRequiredMixin, UpdateView):
    model = SourceDocument
    form_class = StaffDocumentForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:documents")

    def form_valid(self, form):
        messages.success(self.request, "Document saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": self.object.title,
                "cancel_url": reverse("staff:documents"),
                "public_url": self.object.get_absolute_url(),
                "delete_url": reverse("staff:document-delete", args=[self.object.pk]),
            }
        )
        return context


class DocumentDeleteView(StaffRequiredMixin, DeleteView):
    model = SourceDocument
    template_name = "staff/confirm_delete.html"
    success_url = reverse_lazy("staff:documents")

    def form_valid(self, form):
        messages.success(self.request, "Document removed.")
        return super().form_valid(form)


class EvidenceListView(StaffRecordListView):
    model = Evidence
    queryset = Evidence.objects.select_related("project", "source_document")
    search_fields = ("claim", "project__name")
    heading = "Evidence"
    lede = "Label whether a cited source supports each claim. This is not a guilt score."
    create_url = "staff:evidence-create"
    row_template = "staff/rows/evidence.html"
    columns = ("Claim", "Project", "Status")


class EvidenceCreateView(StaffRequiredMixin, CreateView):
    model = Evidence
    form_class = StaffEvidenceForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:evidence")

    def form_valid(self, form):
        messages.success(self.request, "Evidence saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"heading": "New evidence record", "cancel_url": reverse("staff:evidence")})
        return context


class EvidenceUpdateView(StaffRequiredMixin, UpdateView):
    model = Evidence
    form_class = StaffEvidenceForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:evidence")

    def form_valid(self, form):
        messages.success(self.request, "Evidence saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Edit evidence",
                "cancel_url": reverse("staff:evidence"),
                "delete_url": reverse("staff:evidence-delete", args=[self.object.pk]),
            }
        )
        return context


class EvidenceDeleteView(StaffRequiredMixin, DeleteView):
    model = Evidence
    template_name = "staff/confirm_delete.html"
    success_url = reverse_lazy("staff:evidence")

    def form_valid(self, form):
        messages.success(self.request, "Evidence record removed.")
        return super().form_valid(form)


class PolicyListView(StaffRecordListView):
    model = Policy
    queryset = Policy.objects.select_related("institution")
    search_fields = ("title", "institution__name")
    heading = "Policies"
    lede = "Policy files linked to institutions and source documents."
    create_url = "staff:policy-create"
    row_template = "staff/rows/policy.html"
    columns = ("Policy", "Type", "Status")


class PolicyCreateView(StaffRequiredMixin, CreateView):
    model = Policy
    form_class = StaffPolicyForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:policies")

    def form_valid(self, form):
        messages.success(self.request, "Policy saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"heading": "New policy", "cancel_url": reverse("staff:policies")})
        return context


class PolicyUpdateView(StaffRequiredMixin, UpdateView):
    model = Policy
    form_class = StaffPolicyForm
    template_name = "staff/form.html"
    success_url = reverse_lazy("staff:policies")

    def form_valid(self, form):
        messages.success(self.request, "Policy saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": self.object.title,
                "cancel_url": reverse("staff:policies"),
                "public_url": self.object.get_absolute_url(),
                "delete_url": reverse("staff:policy-delete", args=[self.object.pk]),
            }
        )
        return context


class PolicyDeleteView(StaffRequiredMixin, DeleteView):
    model = Policy
    template_name = "staff/confirm_delete.html"
    success_url = reverse_lazy("staff:policies")

    def form_valid(self, form):
        messages.success(self.request, "Policy removed.")
        return super().form_valid(form)


class InvestigationListView(StaffRecordListView):
    model = Investigation
    queryset = Investigation.objects.select_related("project", "user")
    search_fields = ("title", "observation", "project__name", "location")
    heading = "Investigations"
    lede = "Every citizen observation. Review status here — an observation is not a finding."
    create_url = ""
    row_template = "staff/rows/investigation.html"
    columns = ("Observation", "Project", "Status")


class InvestigationUpdateView(StaffRequiredMixin, UpdateView):
    model = Investigation
    form_class = StaffInvestigationForm
    template_name = "staff/form.html"
    queryset = Investigation.objects.select_related("project")

    def get_success_url(self):
        return reverse("staff:investigation-edit", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Investigation saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": self.object.title,
                "cancel_url": reverse("staff:investigations"),
                "public_url": self.object.get_absolute_url(),
                "delete_url": reverse("staff:investigation-delete", args=[self.object.pk]),
            }
        )
        return context


class InvestigationDeleteView(StaffRequiredMixin, DeleteView):
    model = Investigation
    template_name = "staff/confirm_delete.html"
    success_url = reverse_lazy("staff:investigations")

    def form_valid(self, form):
        messages.success(self.request, "Investigation removed.")
        return super().form_valid(form)


class ReportListView(StaffRecordListView):
    model = IssueReport
    queryset = IssueReport.objects.select_related("project", "user")
    search_fields = ("title", "project__name")
    heading = "Reports"
    lede = "Review, verify, and publish structured reports. They stay private until you publish."
    create_url = ""
    row_template = "staff/rows/report.html"
    columns = ("Report", "Status", "Public")


class ReportUpdateView(StaffRequiredMixin, UpdateView):
    model = IssueReport
    form_class = StaffReportForm
    template_name = "staff/form.html"

    def get_success_url(self):
        return reverse("staff:report-edit", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Report saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": self.object.title,
                "cancel_url": reverse("staff:reports"),
                "public_url": self.object.get_absolute_url(),
                "delete_url": reverse("staff:report-delete", args=[self.object.pk]),
            }
        )
        return context


class ReportDeleteView(StaffRequiredMixin, DeleteView):
    model = IssueReport
    template_name = "staff/confirm_delete.html"
    success_url = reverse_lazy("staff:reports")

    def form_valid(self, form):
        messages.success(self.request, "Report removed.")
        return super().form_valid(form)


class UserListView(StaffRecordListView):
    model = User
    search_fields = ("username", "email", "display_name", "first_name", "last_name")
    heading = "Accounts"
    lede = "Activate, deactivate, or grant staff access. Do not change your own staff flag."
    create_url = ""
    row_template = "staff/rows/user.html"
    columns = ("Account", "Staff", "Active")


class UserUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = StaffUserForm
    template_name = "staff/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("staff:user-edit", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Account saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"heading": self.object.public_name(), "cancel_url": reverse("staff:users")})
        return context
