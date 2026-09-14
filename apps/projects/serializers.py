from rest_framework import serializers

from apps.projects.models import BudgetAllocation, Institution, Project, TimelineEvent
from apps.sources.models import Evidence, SourceDocument


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "institution_type",
            "website",
            "location",
            "created_at",
            "updated_at",
        )


class SourceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceDocument
        fields = (
            "id",
            "title",
            "publisher",
            "source_url",
            "document_type",
            "publication_date",
            "description",
            "verification_level",
            "created_at",
            "updated_at",
        )


class EvidenceSerializer(serializers.ModelSerializer):
    source_document = SourceDocumentSerializer(read_only=True)

    class Meta:
        model = Evidence
        fields = (
            "id",
            "project",
            "claim",
            "evidence_text",
            "source_document",
            "page_number",
            "source_url",
            "verification_status",
            "notes",
            "created_at",
            "updated_at",
        )


class BudgetAllocationSerializer(serializers.ModelSerializer):
    formatted_amount = serializers.CharField(source="format_amount", read_only=True)
    source_document = SourceDocumentSerializer(read_only=True)

    class Meta:
        model = BudgetAllocation
        fields = (
            "id",
            "financial_year",
            "amount",
            "formatted_amount",
            "currency",
            "allocation_type",
            "source_document",
            "notes",
            "created_at",
        )


class TimelineEventSerializer(serializers.ModelSerializer):
    evidence_unavailable = serializers.SerializerMethodField()
    stage_label = serializers.CharField(source="get_stage_display", read_only=True)
    formatted_amount = serializers.CharField(source="format_amount", read_only=True)

    class Meta:
        model = TimelineEvent
        fields = (
            "id",
            "stage",
            "stage_label",
            "title",
            "description",
            "amount",
            "formatted_amount",
            "occurred_on",
            "evidence",
            "evidence_unavailable",
        )

    def get_evidence_unavailable(self, obj):
        return not bool(obj.evidence_id)


class ProjectListSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    formatted_amount = serializers.CharField(source="format_amount", read_only=True)
    evidence_coverage = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "location",
            "county",
            "ward",
            "institution",
            "contractor",
            "allocated_amount",
            "formatted_amount",
            "currency",
            "financial_year",
            "status",
            "evidence_coverage",
            "created_at",
            "updated_at",
        )

    def get_evidence_coverage(self, obj):
        from apps.core.services.coverage import calculate_evidence_coverage

        coverage = calculate_evidence_coverage(obj)
        return {
            "percent": coverage["percent"],
            "supported": coverage["supported"],
            "total_claims": coverage["total_claims"],
        }


class ProjectDetailSerializer(ProjectListSerializer):
    allocations = BudgetAllocationSerializer(many=True, read_only=True)
    evidence_items = EvidenceSerializer(many=True, read_only=True)
    source_documents = SourceDocumentSerializer(many=True, read_only=True)
    timeline = serializers.SerializerMethodField()
    missing_information = serializers.SerializerMethodField()

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + (
            "description",
            "start_date",
            "expected_completion_date",
            "actual_completion_date",
            "allocations",
            "evidence_items",
            "source_documents",
            "timeline",
            "missing_information",
        )

    def get_timeline(self, obj):
        from apps.core.services.timeline import build_project_timeline

        payload = []
        for item in build_project_timeline(obj):
            event = item["event"]
            payload.append(
                {
                    "stage": item["stage"],
                    "stage_label": item["stage_label"],
                    "has_event": item["has_event"],
                    "has_evidence": item["has_evidence"],
                    "evidence_unavailable": item["evidence_unavailable"],
                    "title": event.title if event else None,
                    "description": event.description if event else None,
                    "amount": str(event.amount) if event and event.amount is not None else None,
                    "occurred_on": event.occurred_on if event else None,
                }
            )
        return payload

    def get_missing_information(self, obj):
        from apps.core.services.coverage import calculate_evidence_coverage

        return calculate_evidence_coverage(obj)["missing"]

    def get_evidence_coverage(self, obj):
        from apps.core.services.coverage import calculate_evidence_coverage

        coverage = calculate_evidence_coverage(obj)
        return {
            "percent": coverage["percent"],
            "supported": coverage["supported"],
            "total_claims": coverage["total_claims"],
            "verified": coverage["verified"],
            "partially_verified": coverage["partially_verified"],
            "conflicting": coverage["conflicting"],
            "unknown": coverage["unknown"],
            "level": coverage["level"],
        }
