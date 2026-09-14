from rest_framework import serializers

from apps.investigations.models import Investigation
from apps.projects.models import Project


class InvestigationSerializer(serializers.ModelSerializer):
    project_id = serializers.PrimaryKeyRelatedField(
        source="project",
        queryset=Project.objects.all(),
        write_only=True,
    )
    project = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Investigation
        fields = (
            "id",
            "project",
            "project_id",
            "title",
            "observation",
            "location",
            "observed_at",
            "official_information",
            "difference_description",
            "evidence_description",
            "attachment",
            "verification_status",
            "is_anonymous",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "verification_status",
            "is_anonymous",
            "created_at",
            "updated_at",
            "project",
        )
        extra_kwargs = {
            "title": {"required": False, "allow_blank": True},
            "attachment": {"required": False},
            "evidence_description": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        request = self.context["request"]
        if request.user.is_authenticated:
            validated_data["user"] = request.user
            validated_data["is_anonymous"] = False
        else:
            validated_data["user"] = None
            validated_data["is_anonymous"] = True
        if not validated_data.get("title"):
            validated_data["title"] = f"Citizen observation: {validated_data['project'].name}"
        return super().create(validated_data)
