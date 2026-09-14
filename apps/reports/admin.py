from django.contrib import admin

from .models import IssueReport


@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "user", "status", "is_public", "created_at")
    search_fields = (
        "title",
        "official_information",
        "citizen_observation",
        "potential_discrepancy",
        "project__name",
    )
    list_filter = ("status", "is_public")
    autocomplete_fields = ["project", "investigation", "user"]
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
