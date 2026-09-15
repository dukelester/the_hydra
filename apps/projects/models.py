from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.core.models import UUIDModel
from apps.core.utils import unique_slug


class InstitutionType(models.TextChoices):
    COUNTY_DEPARTMENT = "county_department", "County Department"
    COUNTY_GOVERNMENT = "county_government", "County Government"
    NATIONAL_MINISTRY = "national_ministry", "National Ministry"
    AGENCY = "agency", "Agency"
    OVERSIGHT = "oversight", "Oversight Body"
    OTHER = "other", "Other"


class ProjectStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    APPROVED = "approved", "Approved"
    PROCUREMENT = "procurement", "Procurement"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    DELAYED = "delayed", "Delayed"
    UNKNOWN = "unknown", "Unknown"


class ProjectCategory(models.TextChoices):
    WATER = "water", "Water"
    HEALTH = "health", "Health"
    EDUCATION = "education", "Education"
    ROADS = "roads", "Roads"
    ENERGY = "energy", "Energy"
    SANITATION = "sanitation", "Sanitation"
    AGRICULTURE = "agriculture", "Agriculture"
    MARKETS = "markets", "Markets"
    OTHER = "other", "Other"


class AllocationType(models.TextChoices):
    ORIGINAL = "original", "Original allocation"
    SUPPLEMENTARY = "supplementary", "Supplementary"
    REVISED = "revised", "Revised"
    RECURRENT = "recurrent", "Recurrent"
    DEVELOPMENT = "development", "Development"


class TimelineStage(models.TextChoices):
    ALLOCATION = "allocation", "Allocation"
    APPROVAL = "approval", "Approval"
    PROCUREMENT = "procurement", "Procurement"
    CONTRACT = "contract", "Contract"
    IMPLEMENTATION = "implementation", "Implementation"
    COMPLETION = "completion", "Completion"


TIMELINE_STAGE_ORDER = [
    TimelineStage.ALLOCATION,
    TimelineStage.APPROVAL,
    TimelineStage.PROCUREMENT,
    TimelineStage.CONTRACT,
    TimelineStage.IMPLEMENTATION,
    TimelineStage.COMPLETION,
]


class Institution(UUIDModel):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField(blank=True)
    institution_type = models.CharField(
        max_length=40,
        choices=InstitutionType.choices,
        default=InstitutionType.COUNTY_DEPARTMENT,
    )
    website = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("institutions:detail", kwargs={"slug": self.slug})


class Project(UUIDModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField()
    category = models.CharField(
        max_length=40,
        choices=ProjectCategory.choices,
        default=ProjectCategory.OTHER,
    )
    location = models.CharField(max_length=255)
    county = models.CharField(max_length=120, db_index=True)
    constituency = models.CharField(max_length=120, blank=True, db_index=True)
    ward = models.CharField(max_length=120, blank=True)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    contractor = models.CharField(
        max_length=255,
        blank=True,
        help_text="Implementing contractor or firm as stated in source documents. Leave blank if unknown.",
    )
    allocated_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default="KES")
    financial_year = models.CharField(max_length=20, blank=True)
    start_date = models.DateField(null=True, blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=ProjectStatus.choices,
        default=ProjectStatus.UNKNOWN,
        db_index=True,
    )
    is_featured = models.BooleanField(default=False)
    is_demo = models.BooleanField(
        default=False,
        help_text="Marks records created as labelled demo data.",
    )
    source_documents = models.ManyToManyField(
        "sources.SourceDocument",
        blank=True,
        related_name="projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["county", "status"]),
            models.Index(fields=["county", "constituency"]),
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
            models.Index(fields=["ward"]),
            models.Index(fields=["contractor"]),
            models.Index(fields=["financial_year"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("projects:detail", kwargs={"slug": self.slug})

    def format_amount(self):
        if self.allocated_amount is None:
            return "Information unavailable"
        amount = f"{self.allocated_amount:,.0f}"
        if self.currency == "KES":
            return f"KSh {amount}"
        return f"{self.currency} {amount}"


class BudgetAllocation(UUIDModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="allocations")
    financial_year = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default="KES")
    allocation_type = models.CharField(
        max_length=30,
        choices=AllocationType.choices,
        default=AllocationType.DEVELOPMENT,
    )
    source_document = models.ForeignKey(
        "sources.SourceDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="allocations",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-financial_year", "-created_at"]

    def __str__(self):
        return f"{self.project.name} — {self.financial_year}"

    def format_amount(self):
        amount = f"{self.amount:,.0f}"
        if self.currency == "KES":
            return f"KSh {amount}"
        return f"{self.currency} {amount}"


class TimelineEvent(UUIDModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="timeline_events")
    stage = models.CharField(max_length=30, choices=TimelineStage.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default="KES")
    occurred_on = models.DateField(null=True, blank=True)
    evidence = models.ForeignKey(
        "sources.Evidence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timeline_events",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"{self.project.name}: {self.get_stage_display()}"

    def format_amount(self):
        if self.amount is None:
            return ""
        amount = f"{self.amount:,.0f}"
        if self.currency == "KES":
            return f"KSh {amount}"
        return f"{self.currency} {amount}"


class ProjectView(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_views",
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-viewed_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "project"], name="unique_user_project_view"),
        ]
        indexes = [models.Index(fields=["user", "-viewed_at"])]

    def __str__(self):
        return f"{self.user} viewed {self.project}"


class ProjectFollow(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_follows",
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="follows")
    is_tracked = models.BooleanField(default=False)
    is_favourite = models.BooleanField(default=False)
    last_seen_updated_at = models.DateTimeField()
    last_seen_status = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "project"], name="unique_user_project_follow"),
        ]

    def __str__(self):
        return f"{self.user} follows {self.project}"

    def has_record_update(self):
        return self.project.updated_at > self.last_seen_updated_at

    def has_status_change(self):
        return bool(self.last_seen_status) and self.last_seen_status != self.project.status

    def last_seen_status_label(self):
        if not self.last_seen_status:
            return "Not recorded"
        try:
            return ProjectStatus(self.last_seen_status).label
        except ValueError:
            return self.last_seen_status
