from pathlib import Path

from django.db import models
from django.urls import reverse
from django.utils.text import get_valid_filename

from apps.core.models import UUIDModel
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


class ExtractionStatus(models.TextChoices):
    EMPTY = "empty", "No file"
    READY = "ready", "Searchable"
    FAILED = "failed", "Could not read file"
    SKIPPED = "skipped", "Type not extracted"


class SourceDocument(UUIDModel):
    title = models.CharField(max_length=255, db_index=True)
    publisher = models.CharField(max_length=255, db_index=True)
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
    original_filename = models.CharField(max_length=255, blank=True, db_index=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    extracted_text = models.TextField(
        blank=True,
        help_text="Plain text extracted for search. Capped so large files stay usable.",
    )
    extraction_status = models.CharField(
        max_length=20,
        choices=ExtractionStatus.choices,
        default=ExtractionStatus.EMPTY,
        db_index=True,
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
        indexes = [
            models.Index(fields=["document_type", "publication_date"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("sources:detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        extract = kwargs.pop("extract", True)
        previous_file = None
        if self.pk:
            previous_file = (
                SourceDocument.objects.filter(pk=self.pk).values_list("file", flat=True).first()
            )
        if self.file and getattr(self.file, "_committed", True) is False:
            raw_name = Path(self.file.name).name
            if raw_name:
                self.original_filename = get_valid_filename(raw_name)[:255]
            self.file_size = getattr(self.file, "size", None) or self.file_size
        super().save(*args, **kwargs)
        if not extract:
            return
        current_name = self.file.name if self.file else ""
        file_changed = bool(self.file) and previous_file != current_name
        if self.file and (file_changed or (not self.extracted_text and self.extraction_status == ExtractionStatus.EMPTY)):
            from apps.sources.processing import schedule_document_extraction

            schedule_document_extraction(self.pk)
        elif not self.file and (self.extracted_text or self.extraction_status != ExtractionStatus.EMPTY):
            self.extracted_text = ""
            self.extraction_status = ExtractionStatus.EMPTY
            self.original_filename = ""
            self.file_size = None
            super().save(
                update_fields=[
                    "extracted_text",
                    "extraction_status",
                    "original_filename",
                    "file_size",
                    "updated_at",
                ]
            )

    def _store_extracted_text(self, text):
        ext = Path(self.original_filename or self.file.name).suffix.lower()
        if ext not in {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md"}:
            status = ExtractionStatus.SKIPPED
            stored = ""
        elif text:
            status = ExtractionStatus.READY
            stored = text
        else:
            status = ExtractionStatus.FAILED
            stored = ""
        self.extracted_text = stored
        self.extraction_status = status
        if self.file:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(
            update_fields=["extracted_text", "extraction_status", "file_size", "updated_at"]
        )

    def file_extension(self):
        return Path(self.original_filename or (self.file.name if self.file else "")).suffix.lower()

    def preview_kind(self):
        ext = self.file_extension()
        if ext == ".pdf":
            return "pdf"
        if ext == ".docx":
            return "docx"
        if ext in {".xlsx", ".csv"}:
            return "spreadsheet"
        if ext in {".jpg", ".jpeg", ".png", ".webp"}:
            return "image"
        return "none"

    def format_file_size(self):
        if not self.file_size:
            return ""
        size = float(self.file_size)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                if unit == "B":
                    return f"{int(size)} B"
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{self.file_size} B"

    def snippet_for(self, query, radius=90):
        if not query or not self.extracted_text:
            return ""
        haystack = self.extracted_text
        needle = query.lower()
        index = haystack.lower().find(needle)
        if index < 0:
            return haystack[:180].strip()
        start = max(0, index - radius)
        end = min(len(haystack), index + len(query) + radius)
        excerpt = haystack[start:end].strip()
        if start > 0:
            excerpt = "…" + excerpt
        if end < len(haystack):
            excerpt = excerpt + "…"
        return excerpt


class Evidence(UUIDModel):
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
        ordering = ["created_at", "id"]
        verbose_name_plural = "evidence"

    def __str__(self):
        return f"{self.project.name}: {self.claim[:80]}"

    def has_source(self):
        return bool(self.source_document_id or self.source_url or self.evidence_text)
