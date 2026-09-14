from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from apps.policies.models import Policy
from apps.policies.serializers import PolicySerializer


class PolicyListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PolicySerializer
    queryset = Policy.objects.select_related("institution", "source_document")
