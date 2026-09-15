from django.contrib.auth.validators import UnicodeUsernameValidator
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django import forms

from apps.accounts.models import AreaWatch, User, UserRole
from apps.core.uploads import validate_upload
from apps.investigations.models import Investigation, store_investigation_files
from apps.projects.area import area_counties, constituencies_for, wards_for
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


class RegisterIdentityForm(StyledFormMixin, forms.Form):
    username = forms.CharField(
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        help_text="Letters, digits, and @/./+/-/_ only.",
    )
    display_name = forms.CharField(
        max_length=150,
        required=False,
        label="Display name",
        help_text="Optional. Shown on your dashboard instead of the username.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Choose a username"
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["display_name"].widget.attrs["placeholder"] = "Optional public name"
        self.fields["display_name"].widget.attrs["autocomplete"] = "nickname"
        self._style_fields()

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username


class RegisterForm(StyledFormMixin, UserCreationForm):
    display_name = forms.CharField(max_length=150, required=False, label="Display name")
    agree_to_terms = forms.BooleanField(
        required=True,
        label="I agree to the terms of use",
        error_messages={"required": "You must agree to the terms of use to create an account."},
    )

    class Meta:
        model = User
        fields = ("username", "display_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Choose a username"
        self.fields["display_name"].widget.attrs["placeholder"] = "Optional public name"
        self.fields["password1"].widget.attrs["placeholder"] = "Password"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
        self.fields["username"].help_text = "Letters, digits, and @/./+/-/_ only."
        self.fields["password1"].help_text = "At least 8 characters. Avoid common words or a password that is only numbers."
        self.fields["password2"].help_text = "Enter the same password again."
        self._style_fields()


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "display_name",
            "first_name",
            "last_name",
            "email",
            "affiliation",
            "role",
            "county",
            "constituency",
            "ward",
            "location",
            "website",
            "bio",
        )
        labels = {
            "display_name": "Display name",
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email",
            "affiliation": "Affiliation",
            "role": "How you use H.Y.D.R.A.",
            "county": "County",
            "constituency": "Constituency",
            "ward": "Ward",
            "location": "Town or area",
            "website": "Website",
            "bio": "About you",
        }
        help_texts = {
            "display_name": "Shown on your dashboard and avatar. Your username stays the same.",
            "first_name": "Optional. Used only on your profile.",
            "last_name": "Optional. Used only on your profile.",
            "email": "Optional, but needed to reset a forgotten password.",
            "affiliation": "Newsroom, university, department, or organisation — if you want it recorded.",
            "role": "Optional. Helps us understand who uses the record.",
            "county": "Optional. Used if you track your county.",
            "constituency": "Optional. Narrows the county feed.",
            "ward": "Optional. Narrows the county feed further.",
            "location": "Optional. Town or neighbourhood.",
            "website": "Optional. A public page, not a private profile.",
            "bio": "Optional. A short note about how you use this platform.",
        }
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Optional. Keep it short."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            self.fields[name].required = False
        self.fields["role"].choices = [("", "Prefer not to say")] + list(UserRole.choices)
        self.fields["display_name"].widget.attrs["placeholder"] = "How should we address you?"
        self.fields["first_name"].widget.attrs["placeholder"] = "Optional"
        self.fields["last_name"].widget.attrs["placeholder"] = "Optional"
        self.fields["email"].widget.attrs["placeholder"] = "you@example.com"
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["affiliation"].widget.attrs["placeholder"] = "Optional organisation"
        self.fields["county"].widget.attrs["placeholder"] = "Optional county"
        self.fields["constituency"].widget.attrs["placeholder"] = "Optional constituency"
        self.fields["ward"].widget.attrs["placeholder"] = "Optional ward"
        self.fields["location"].widget.attrs["placeholder"] = "Optional town"
        self.fields["website"].widget.attrs["placeholder"] = "https://"
        self.fields["website"].widget.attrs["autocomplete"] = "url"
        self._style_fields()


class AreaWatchForm(StyledFormMixin, forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        kwargs.pop("counties", None)
        kwargs.pop("constituencies", None)
        kwargs.pop("wards", None)
        kwargs.pop("instance", None)
        self.user = user
        super().__init__(*args, **kwargs)
        county = self._posted_value("county")
        constituency = self._posted_value("constituency")
        if constituency and constituency not in constituencies_for(county):
            constituency = ""

        counties = area_counties()
        self.fields["county"] = forms.ChoiceField(
            choices=[("", "Choose a county")] + [(name, name) for name in counties],
            required=True,
            label="County",
        )
        const_choices = constituencies_for(county)
        self.fields["constituency"] = forms.ChoiceField(
            choices=[("", "All constituencies" if county else "Choose a county first")]
            + [(name, name) for name in const_choices],
            required=False,
            label="Constituency",
        )
        ward_choices = wards_for(county, constituency)
        self.fields["ward"] = forms.ChoiceField(
            choices=[("", "All wards" if constituency else "Choose a constituency first")]
            + [(name, name) for name in ward_choices],
            required=False,
            label="Ward",
        )
        if not county:
            self.fields["constituency"].widget.attrs["disabled"] = True
        if not constituency:
            self.fields["ward"].widget.attrs["disabled"] = True
        self._style_fields()
        self.fields["county"].widget.attrs.update(
            {
                "hx-get": reverse("accounts:area-options"),
                "hx-trigger": "change",
                "hx-target": "#area-dependent",
                "hx-swap": "innerHTML",
                "autocomplete": "off",
            }
        )
        self.fields["constituency"].widget.attrs.update(
            {
                "hx-get": reverse("accounts:area-options"),
                "hx-trigger": "change",
                "hx-include": "#id_county",
                "hx-target": "#ward-field",
                "hx-swap": "outerHTML",
                "autocomplete": "off",
            }
        )
        self.fields["ward"].widget.attrs.update({"autocomplete": "off"})

    def _posted_value(self, name):
        if self.is_bound:
            return (self.data.get(name) or "").strip()
        return ""

    def clean_county(self):
        county = (self.cleaned_data.get("county") or "").strip()
        if not county:
            raise forms.ValidationError("Choose a county to track.")
        return county

    def clean(self):
        cleaned = super().clean()
        county = cleaned.get("county") or ""
        constituency = (cleaned.get("constituency") or "").strip()
        ward = (cleaned.get("ward") or "").strip()
        if constituency and constituency not in constituencies_for(county):
            self.add_error("constituency", "Choose a constituency in that county.")
        if ward and not constituency:
            self.add_error("ward", "Choose a constituency before a ward.")
        elif ward and ward not in wards_for(county, constituency):
            self.add_error("ward", "Choose a ward in that constituency.")
        if self.user and self.user.pk and not self.errors:
            watches = self.user.area_watches.all()
            if watches.count() >= AreaWatch.MAX_PER_USER:
                raise forms.ValidationError(
                    f"You can track up to {AreaWatch.MAX_PER_USER} areas. Remove one to add another."
                )
            if watches.filter(county=county, constituency=constituency, ward=ward).exists():
                raise forms.ValidationError("You are already tracking this area.")
        cleaned["constituency"] = constituency
        cleaned["ward"] = ward
        return cleaned

    def save(self):
        from django.utils import timezone

        watch = AreaWatch.objects.create(
            user=self.user,
            county=self.cleaned_data["county"],
            constituency=self.cleaned_data.get("constituency") or "",
            ward=self.cleaned_data.get("ward") or "",
            last_seen_at=timezone.now(),
        )
        if not (self.user.county or "").strip():
            self.user.county = watch.county
            self.user.constituency = watch.constituency
            self.user.ward = watch.ward
            self.user.save(update_fields=["county", "constituency", "ward"])
        self.user.sync_area_tracking()
        return watch


class StyledPasswordResetForm(StyledFormMixin, PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "Email"
        self.fields["email"].help_text = (
            "Use the address on your profile. If you never added one, sign in and set it there, "
            "or change your password from the profile page while logged in."
        )
        self.fields["email"].widget.attrs["placeholder"] = "you@example.com"
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self._style_fields()


class StyledSetPasswordForm(StyledFormMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password2"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password1"].widget.attrs["placeholder"] = "New password"
        self.fields["new_password2"].widget.attrs["placeholder"] = "Confirm new password"
        self.fields["new_password1"].help_text = (
            "At least 8 characters. Avoid common words or a password that is only numbers."
        )
        self.fields["new_password2"].help_text = "Enter the same password again."
        self._style_fields()


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs["autocomplete"] = "current-password"
        self.fields["old_password"].widget.attrs["placeholder"] = "Current password"
        self.fields["new_password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password2"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password1"].widget.attrs["placeholder"] = "New password"
        self.fields["new_password2"].widget.attrs["placeholder"] = "Confirm new password"
        self.fields["new_password1"].help_text = (
            "At least 8 characters. Avoid common words or a password that is only numbers."
        )
        self.fields["new_password2"].help_text = "Enter the same password again."
        self._style_fields()


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []
        items = data if isinstance(data, (list, tuple)) else [data]
        return [super().clean(item, initial) for item in items]


class InvestigationForm(StyledFormMixin, forms.ModelForm):
    attachment = MultipleFileField(
        required=False,
        widget=MultipleFileInput(
            attrs={"accept": ".pdf,.docx,.xlsx,.csv,.png,.jpg,.jpeg,.webp", "multiple": True}
        ),
    )

    class Meta:
        model = Investigation
        fields = (
            "observation",
            "location",
            "observed_at",
            "official_information",
            "difference_description",
            "evidence_description",
        )
        labels = {
            "observation": "What did you observe?",
            "location": "Where?",
            "observed_at": "When?",
            "official_information": "Official information on record",
            "difference_description": "What is different?",
            "evidence_description": "What does your evidence show? (optional)",
        }
        widgets = {
            "observation": forms.Textarea(attrs={"rows": 6, "placeholder": "Describe what you saw, in plain language."}),
            "location": forms.TextInput(attrs={"placeholder": "Place, ward, or site name"}),
            "official_information": forms.Textarea(attrs={"rows": 4, "placeholder": "Quote or paraphrase the official claim you are comparing."}),
            "difference_description": forms.Textarea(attrs={"rows": 4, "placeholder": "What does not match, and why it matters."}),
            "evidence_description": forms.Textarea(attrs={"rows": 3, "placeholder": "What does the photo or file show?"}),
            "observed_at": forms.DateInput(attrs={"type": "date"}),
        }
        help_texts = {
            "observation": "Write what you saw or heard at the site. Do not include other people’s personal details.",
            "official_information": "Quote or paraphrase the official claim. Leave it as recorded even if you disagree.",
            "difference_description": "Say clearly what does not match. This is still an observation, not a finding of wrongdoing.",
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        self.user = kwargs.pop("user", None)
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
        max_files = getattr(settings, "THEHYDRA_MAX_UPLOAD_FILES", 8)
        self.fields["attachment"].label = "Upload files (optional)"
        self.fields["attachment"].help_text = (
            f"Optional. Up to {max_files} files, {max_mb} MB each. "
            "PDF, Word (.docx), Excel (.xlsx), CSV, or image. Files are stored on disk and processed after submit."
        )
        if self.user and getattr(self.user, "is_authenticated", False):
            self.fields["hide_account"] = forms.BooleanField(
                required=False,
                label="Do not show my account name on this observation",
                help_text="The observation stays attached to your account so you can find it later. Public and shared copies can be labelled anonymous.",
            )
        self._style_fields()

    def clean_attachment(self):
        files = self.cleaned_data.get("attachment") or []
        max_files = getattr(settings, "THEHYDRA_MAX_UPLOAD_FILES", 8)
        if len(files) > max_files:
            raise forms.ValidationError(f"You can attach up to {max_files} files.")
        for uploaded in files:
            validate_upload(uploaded)
        return files

    def save_files(self, investigation):
        return store_investigation_files(investigation, self.cleaned_data.get("attachment") or [])


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
