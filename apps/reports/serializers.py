from rest_framework import serializers

from apps.investigations.models import Investigation
from apps.reports.models import IssueReport
from apps.reports.services import generate_report_from_investigation


class IssueReportSerializer(serializers.ModelSerializer):
    investigation_id = serializers.PrimaryKeyRelatedField(
        source="investigation",
        queryset=Investigation.objects.all(),
        write_only=True,
        required=False,
    )
    project = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = IssueReport
        fields = (
            "id",
            "project",
            "investigation",
            "investigation_id",
            "title",
            "official_information",
            "citizen_observation",
            "evidence_summary",
            "potential_discrepancy",
            "recommended_next_steps",
            "status",
            "is_public",
            "created_at",
        )
        read_only_fields = (
            "id",
            "project",
            "investigation",
            "is_public",
            "created_at",
            "title",
            "official_information",
            "citizen_observation",
            "evidence_summary",
            "potential_discrepancy",
            "recommended_next_steps",
            "status",
        )

    def create(self, validated_data):
        request = self.context["request"]
        investigation = validated_data["investigation"]
        user = request.user if request.user.is_authenticated else None
        return generate_report_from_investigation(investigation, user=user)
