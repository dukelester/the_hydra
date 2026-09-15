from django import forms

from apps.accounts.models import User
from apps.core.forms import StyledFormMixin
from apps.investigations.models import Investigation
from apps.policies.models import Policy
from apps.projects.models import Institution, Project
from apps.reports.models import IssueReport
from apps.sources.models import Evidence, SourceDocument


class StaffProjectForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            "name",
            "description",
            "category",
            "location",
            "county",
            "constituency",
            "ward",
            "institution",
            "contractor",
            "allocated_amount",
            "currency",
            "financial_year",
            "start_date",
            "expected_completion_date",
            "actual_completion_date",
            "status",
            "is_featured",
            "is_demo",
            "source_documents",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "expected_completion_date": forms.DateInput(attrs={"type": "date"}),
            "actual_completion_date": forms.DateInput(attrs={"type": "date"}),
            "source_documents": forms.SelectMultiple(attrs={"size": 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_documents"].required = False
        self._style_fields()


class StaffInstitutionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Institution
        fields = ("name", "description", "institution_type", "website", "location")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class StaffDocumentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SourceDocument
        fields = (
            "title",
            "publisher",
            "source_url",
            "document_type",
            "publication_date",
            "file",
            "description",
            "verification_level",
            "is_demo",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = False
        self._style_fields()


class StaffEvidenceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Evidence
        fields = (
            "project",
            "claim",
            "evidence_text",
            "source_document",
            "page_number",
            "source_url",
            "verification_status",
            "notes",
        )
        widgets = {
            "claim": forms.Textarea(attrs={"rows": 3}),
            "evidence_text": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class StaffPolicyForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Policy
        fields = (
            "title",
            "description",
            "institution",
            "policy_type",
            "publication_date",
            "source_document",
            "source_url",
            "status",
            "is_demo",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "publication_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class StaffInvestigationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Investigation
        fields = (
            "project",
            "title",
            "observation",
            "location",
            "observed_at",
            "official_information",
            "difference_description",
            "evidence_description",
            "verification_status",
        )
        widgets = {
            "observation": forms.Textarea(attrs={"rows": 5}),
            "official_information": forms.Textarea(attrs={"rows": 4}),
            "difference_description": forms.Textarea(attrs={"rows": 4}),
            "evidence_description": forms.Textarea(attrs={"rows": 3}),
            "observed_at": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class StaffReportForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = IssueReport
        fields = (
            "title",
            "official_information",
            "citizen_observation",
            "evidence_summary",
            "potential_discrepancy",
            "recommended_next_steps",
            "status",
            "is_public",
        )
        widgets = {
            "official_information": forms.Textarea(attrs={"rows": 4}),
            "citizen_observation": forms.Textarea(attrs={"rows": 4}),
            "evidence_summary": forms.Textarea(attrs={"rows": 4}),
            "potential_discrepancy": forms.Textarea(attrs={"rows": 4}),
            "recommended_next_steps": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {"is_public": "Publish on the public record"}
        help_texts = {
            "is_public": "Public reports can be read without signing in. Keep private unless the file is ready.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class StaffUserForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "display_name",
            "first_name",
            "last_name",
            "affiliation",
            "role",
            "county",
            "is_active",
            "is_staff",
        )

    def __init__(self, *args, **kwargs):
        self.actor = kwargs.pop("actor", None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["username"].disabled = True
        self._style_fields()

    def clean(self):
        cleaned = super().clean()
        if (
            self.actor
            and self.instance.pk
            and self.instance.pk == self.actor.pk
            and cleaned.get("is_staff") is False
        ):
            self.add_error("is_staff", "You cannot remove your own staff access.")
        if (
            self.actor
            and self.instance.pk
            and self.instance.pk == self.actor.pk
            and cleaned.get("is_active") is False
        ):
            self.add_error("is_active", "You cannot deactivate your own account.")
        return cleaned
