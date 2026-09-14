from rest_framework import serializers

from apps.policies.models import Policy
from apps.projects.serializers import InstitutionSerializer, SourceDocumentSerializer


class PolicySerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    source_document = SourceDocumentSerializer(read_only=True)

    class Meta:
        model = Policy
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "institution",
            "policy_type",
            "publication_date",
            "source_document",
            "source_url",
            "status",
            "created_at",
            "updated_at",
        )
