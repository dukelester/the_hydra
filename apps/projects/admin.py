from django.contrib import admin

from apps.sources.models import Evidence

from .models import BudgetAllocation, Institution, Project, ProjectFollow, ProjectView, TimelineEvent


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0
    fields = ("claim", "evidence_text", "source_document", "page_number", "verification_status")
    autocomplete_fields = ["source_document"]
    show_change_link = True


class BudgetAllocationInline(admin.TabularInline):
    model = BudgetAllocation
    extra = 0
    autocomplete_fields = ["source_document"]


class TimelineEventInline(admin.TabularInline):
    model = TimelineEvent
    extra = 0
    autocomplete_fields = ["evidence"]
    fields = (
        "stage",
        "title",
        "description",
        "amount",
        "occurred_on",
        "evidence",
        "sort_order",
    )


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_type", "location", "created_at")
    search_fields = ("name", "description", "location")
    list_filter = ("institution_type",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "county",
        "constituency",
        "institution",
        "status",
        "financial_year",
        "allocated_amount",
        "is_featured",
        "is_demo",
    )
    search_fields = ("name", "description", "county", "constituency", "ward", "location", "contractor")
    list_filter = ("status", "category", "county", "financial_year", "is_featured", "is_demo")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["institution"]
    filter_horizontal = ["source_documents"]
    inlines = [BudgetAllocationInline, TimelineEventInline, EvidenceInline]
    date_hierarchy = "created_at"


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = ("project", "financial_year", "amount", "currency", "allocation_type")
    search_fields = ("project__name", "financial_year", "notes")
    list_filter = ("financial_year", "allocation_type", "currency")
    autocomplete_fields = ["project", "source_document"]


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ("project", "stage", "title", "occurred_on", "amount")
    search_fields = ("project__name", "title", "description")
    list_filter = ("stage",)
    autocomplete_fields = ["project", "evidence"]


@admin.register(ProjectView)
class ProjectViewAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "viewed_at")
    search_fields = ("user__username", "project__name")
    autocomplete_fields = ["user", "project"]
    readonly_fields = ("viewed_at",)


@admin.register(ProjectFollow)
class ProjectFollowAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "is_tracked", "is_favourite", "last_seen_status", "created_at")
    list_filter = ("is_tracked", "is_favourite")
    search_fields = ("user__username", "project__name")
    autocomplete_fields = ["user", "project"]
