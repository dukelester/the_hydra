from django.contrib import admin

from .models import Evidence, SourceDocument


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0
    fields = (
        "claim",
        "evidence_text",
        "source_document",
        "page_number",
        "verification_status",
    )
    autocomplete_fields = ["source_document"]
    show_change_link = True


@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "publisher",
        "document_type",
        "verification_level",
        "extraction_status",
        "publication_date",
        "is_demo",
    )
    search_fields = ("title", "publisher", "description", "original_filename", "extracted_text")
    readonly_fields = ("original_filename", "file_size", "extraction_status", "extracted_text")
    list_filter = ("document_type", "verification_level", "is_demo")
    date_hierarchy = "publication_date"


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "short_claim",
        "verification_status",
        "source_document",
        "page_number",
    )
    search_fields = ("claim", "evidence_text", "project__name", "notes")
    list_filter = ("verification_status",)
    autocomplete_fields = ["project", "source_document"]

    @admin.display(description="Claim")
    def short_claim(self, obj):
        return obj.claim[:80]
