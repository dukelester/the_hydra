from django.db import models
from django.urls import reverse

from apps.core.uploads import SafeUploadTo, validate_upload


class DocumentType(models.TextChoices):
    BUDGET = "budget", "Budget"
    PROCUREMENT = "procurement", "Procurement"
    CONTRACT = "contract", "Contract"
    POLICY = "policy", "Policy"
    AUDIT = "audit", "Audit"
    GOVERNMENT_REPORT = "government_report", "Government Report"
    TENDER = "tender", "Tender"
    PROJECT_REPORT = "project_report", "Project Report"
    OTHER = "other", "Other"


class VerificationLevel(models.TextChoices):
    OFFICIAL = "official", "Official"
    VERIFIED = "verified", "Verified"
    UNVERIFIED = "unverified", "Unverified"
    UNKNOWN = "unknown", "Unknown"


class EvidenceVerificationStatus(models.TextChoices):
    VERIFIED = "verified", "Verified"
    PARTIALLY_VERIFIED = "partially_verified", "Partially Verified"
    CONFLICTING = "conflicting", "Conflicting"
    UNKNOWN = "unknown", "Unknown"


class SourceDocument(models.Model):
    title = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    source_url = models.URLField(blank=True)
    document_type = models.CharField(
        max_length=40,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )
    publication_date = models.DateField(null=True, blank=True)
    file = models.FileField(
        upload_to=SafeUploadTo("documents"),
        blank=True,
        validators=[validate_upload],
    )
    description = models.TextField(blank=True)
    verification_level = models.CharField(
        max_length=20,
        choices=VerificationLevel.choices,
        default=VerificationLevel.UNKNOWN,
    )
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publication_date", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("sources:detail", kwargs={"pk": self.pk})


class Evidence(models.Model):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="evidence_items",
    )
    claim = models.TextField(help_text="The statement being supported or examined.")
    evidence_text = models.TextField(
        blank=True,
        help_text="What the source actually says. Leave blank if unavailable.",
    )
    source_document = models.ForeignKey(
        SourceDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidence_items",
    )
    page_number = models.PositiveIntegerField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    verification_status = models.CharField(
        max_length=30,
        choices=EvidenceVerificationStatus.choices,
        default=EvidenceVerificationStatus.UNKNOWN,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "evidence"

    def __str__(self):
        return f"{self.project.name}: {self.claim[:80]}"

    def has_source(self):
        return bool(self.source_document_id or self.source_url or self.evidence_text)
