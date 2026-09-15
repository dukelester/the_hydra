from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import get_valid_filename

from apps.core.models import UUIDModel
from apps.core.uploads import SafeUploadTo, validate_upload


class InvestigationVerificationStatus(models.TextChoices):
    UNVERIFIED = "unverified", "Unverified"
    UNDER_REVIEW = "under_review", "Under Review"
    VERIFIED = "verified", "Verified"
    DISPUTED = "disputed", "Disputed"


class Investigation(UUIDModel):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="investigations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="investigations",
    )
    title = models.CharField(max_length=255, blank=True)
    observation = models.TextField(help_text="What did you observe?")
    location = models.CharField(max_length=255, help_text="Where did you observe it?")
    observed_at = models.DateField(help_text="When did you observe it?")
    official_information = models.TextField(
        help_text="What official information are you comparing against?"
    )
    difference_description = models.TextField(help_text="Describe the difference.")
    evidence_description = models.TextField(
        blank=True,
        help_text="Describe any supporting evidence you are submitting.",
    )
    attachment = models.FileField(
        upload_to=SafeUploadTo("investigations"),
        blank=True,
        validators=[validate_upload],
    )
    verification_status = models.CharField(
        max_length=30,
        choices=InvestigationVerificationStatus.choices,
        default=InvestigationVerificationStatus.UNVERIFIED,
    )
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("investigations:detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = f"Citizen observation: {self.project.name}"
        super().save(*args, **kwargs)

    def file_count(self):
        stored = self.files.count()
        if stored:
            return stored
        return 1 if self.attachment else 0


class InvestigationAttachment(UUIDModel):
    investigation = models.ForeignKey(
        Investigation,
        on_delete=models.CASCADE,
        related_name="files",
    )
    file = models.FileField(
        upload_to=SafeUploadTo("investigations"),
        validators=[validate_upload],
    )
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return self.original_filename or self.file.name

    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = get_valid_filename(self.file.name)[:255]
        if self.file and not self.file_size:
            self.file_size = getattr(self.file, "size", None)
        super().save(*args, **kwargs)


def store_investigation_files(investigation, uploads):
    saved = []
    for uploaded in uploads or []:
        if not uploaded:
            continue
        item = InvestigationAttachment(
            investigation=investigation,
            original_filename=get_valid_filename(getattr(uploaded, "name", "") or "file")[:255],
            file_size=getattr(uploaded, "size", None),
        )
        item.file = uploaded
        item.save()
        saved.append(item)
    if saved and not investigation.attachment:
        investigation.attachment = saved[0].file.name
        investigation.save(update_fields=["attachment", "updated_at"])
    return saved
