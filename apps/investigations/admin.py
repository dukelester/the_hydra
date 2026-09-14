from django.contrib import admin

from .models import Investigation


@admin.register(Investigation)
class InvestigationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "user",
        "observed_at",
        "verification_status",
        "is_anonymous",
        "created_at",
    )
    search_fields = (
        "title",
        "observation",
        "location",
        "official_information",
        "project__name",
    )
    list_filter = ("verification_status", "is_anonymous", "observed_at")
    autocomplete_fields = ["project", "user"]
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
