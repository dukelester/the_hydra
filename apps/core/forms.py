from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms

from apps.accounts.models import User
from apps.investigations.models import Investigation
from apps.reports.models import IssueReport, ReportStatus


class StyledFormMixin:
    def _style_fields(self):
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "form-file")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-input")
            if field.required:
                widget.attrs.setdefault("aria-required", "true")


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["username"].widget.attrs["placeholder"] = "Username"
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"
        self.fields["password"].widget.attrs["placeholder"] = "Password"
        self._style_fields()


class RegisterForm(StyledFormMixin, UserCreationForm):
    display_name = forms.CharField(max_length=150, required=False, label="Display name")

    class Meta:
        model = User
        fields = ("username", "display_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Choose a username"
        self.fields["display_name"].widget.attrs["placeholder"] = "Optional public name"
        self.fields["password1"].widget.attrs["placeholder"] = "Password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm password"
        self.fields["username"].help_text = "Letters, digits, and @/./+/-/_ only."
        self._style_fields()


class InvestigationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Investigation
        fields = (
            "observation",
            "location",
            "observed_at",
            "official_information",
            "difference_description",
            "evidence_description",
            "attachment",
        )
        labels = {
            "observation": "What did you observe?",
            "location": "Where?",
            "observed_at": "When?",
            "official_information": "Official information on record",
            "difference_description": "What is different?",
            "evidence_description": "What does your evidence show? (optional)",
            "attachment": "Upload a file (optional)",
        }
        widgets = {
            "observation": forms.Textarea(attrs={"rows": 6, "placeholder": "Describe what you saw, in plain language."}),
            "location": forms.TextInput(attrs={"placeholder": "Place, ward, or site name"}),
            "official_information": forms.Textarea(attrs={"rows": 4, "placeholder": "Quote or paraphrase the official claim you are comparing."}),
            "difference_description": forms.Textarea(attrs={"rows": 4, "placeholder": "What does not match, and why it matters."}),
            "evidence_description": forms.Textarea(attrs={"rows": 3, "placeholder": "What does the photo or file show?"}),
            "observed_at": forms.DateInput(attrs={"type": "date"}),
            "attachment": forms.ClearableFileInput(attrs={"accept": ".pdf,.docx,.xlsx,.csv,.png,.jpg,.jpeg,.webp"}),
        }
        help_texts = {
            "attachment": "Optional. PDF, Word (.docx), Excel (.xlsx), CSV, or image, up to 100 MB. Large files are stored on disk.",
            "observation": "Write what you saw or heard at the site. Do not include other people’s personal details.",
            "official_information": "Quote or paraphrase the official claim. Leave it as recorded even if you disagree.",
            "difference_description": "Say clearly what does not match. This is still an observation, not a finding of wrongdoing.",
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        if self.project and not self.initial.get("official_information"):
            self.initial["official_information"] = self.project.status and (
                f"Official status is recorded as “{self.project.get_status_display()}”"
                + (
                    f" with an allocated amount of {self.project.format_amount()}."
                    if self.project.allocated_amount is not None
                    else "."
                )
            )
        max_mb = settings.THEHYDRA_MAX_UPLOAD_BYTES // (1024 * 1024)
        self.fields["attachment"].help_text = (
            f"Optional. PDF, Word (.docx), Excel (.xlsx), CSV, or image, up to {max_mb} MB. "
            "Large files are stored on disk."
        )
        self._style_fields()


class ReportReviewForm(StyledFormMixin, forms.ModelForm):
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
        )
        widgets = {
            "official_information": forms.Textarea(attrs={"rows": 4}),
            "citizen_observation": forms.Textarea(attrs={"rows": 4}),
            "evidence_summary": forms.Textarea(attrs={"rows": 6}),
            "potential_discrepancy": forms.Textarea(attrs={"rows": 5}),
            "recommended_next_steps": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = [
            (ReportStatus.DRAFT, "Save as draft"),
            (ReportStatus.SUBMITTED, "Submit for review"),
        ]
        self._style_fields()
