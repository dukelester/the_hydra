from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.core.uploads import SafeUploadTo, validate_upload


class InvestigationVerificationStatus(models.TextChoices):
    UNVERIFIED = "unverified", "Unverified"
    UNDER_REVIEW = "under_review", "Under Review"
    VERIFIED = "verified", "Verified"
    DISPUTED = "disputed", "Disputed"


class Investigation(models.Model):
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
