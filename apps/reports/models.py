from django.conf import settings
from django.db import models
from django.urls import reverse


class ReportStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under Review"
    VERIFIED = "verified", "Verified"
    RESOLVED = "resolved", "Resolved"


class IssueReport(models.Model):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    investigation = models.ForeignKey(
        "investigations.Investigation",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
    )
    title = models.CharField(max_length=255)
    official_information = models.TextField()
    citizen_observation = models.TextField()
    evidence_summary = models.TextField()
    potential_discrepancy = models.TextField()
    recommended_next_steps = models.TextField()
    status = models.CharField(
        max_length=30,
        choices=ReportStatus.choices,
        default=ReportStatus.DRAFT,
        db_index=True,
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Reports are private by default and are not published automatically.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("reports:detail", kwargs={"pk": self.pk})
