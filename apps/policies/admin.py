from django.contrib import admin

from .models import Policy


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ("title", "institution", "policy_type", "status", "publication_date")
    search_fields = ("title", "description")
    list_filter = ("policy_type", "status", "is_demo")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["institution", "source_document"]
