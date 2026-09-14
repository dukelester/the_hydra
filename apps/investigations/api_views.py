from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.core.api_permissions import IsOwnerOrStaffOrSession
from apps.core.permissions import SESSION_INVESTIGATIONS, remember_id
from apps.investigations.models import Investigation
from apps.investigations.serializers import InvestigationSerializer


class InvestigationCreateAPIView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = InvestigationSerializer
    queryset = Investigation.objects.all()

    def perform_create(self, serializer):
        investigation = serializer.save()
        remember_id(self.request, SESSION_INVESTIGATIONS, investigation.pk)


class InvestigationDetailAPIView(RetrieveAPIView):
    permission_classes = [IsOwnerOrStaffOrSession]
    serializer_class = InvestigationSerializer
    queryset = Investigation.objects.select_related("project")
