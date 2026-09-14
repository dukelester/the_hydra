from django.db import models
from django.urls import reverse

from apps.core.utils import unique_slug


class PolicyType(models.TextChoices):
    BUDGET = "budget", "Budget Policy"
    PROCUREMENT = "procurement", "Procurement"
    ACCESS_TO_INFO = "access_to_information", "Access to Information"
    OVERSIGHT = "oversight", "Oversight"
    DEVELOPMENT = "development", "Development"
    OTHER = "other", "Other"


class PolicyStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    SUPERSEDED = "superseded", "Superseded"
    UNKNOWN = "unknown", "Unknown"


class Policy(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField()
    institution = models.ForeignKey(
        "projects.Institution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="policies",
    )
    policy_type = models.CharField(
        max_length=40,
        choices=PolicyType.choices,
        default=PolicyType.OTHER,
    )
    publication_date = models.DateField(null=True, blank=True)
    source_document = models.ForeignKey(
        "sources.SourceDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="policies",
    )
    source_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=PolicyStatus.choices,
        default=PolicyStatus.ACTIVE,
    )
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name_plural = "policies"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("policies:detail", kwargs={"slug": self.slug})
