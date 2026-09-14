from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.core.api_permissions import IsOwnerOrStaffOrSession
from apps.core.permissions import (
    SESSION_REPORTS,
    can_create_report_for_investigation,
    remember_id,
)
from apps.reports.models import IssueReport
from apps.reports.serializers import IssueReportSerializer


class ReportCreateAPIView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = IssueReportSerializer
    queryset = IssueReport.objects.all()

    def perform_create(self, serializer):
        investigation = serializer.validated_data.get("investigation")
        if investigation is None:
            raise ValidationError({"investigation_id": "This field is required."})
        if not can_create_report_for_investigation(self.request, investigation):
            raise PermissionDenied("You cannot create a report for this investigation.")
        report = serializer.save()
        remember_id(self.request, SESSION_REPORTS, report.pk)


class ReportDetailAPIView(RetrieveAPIView):
    permission_classes = [IsOwnerOrStaffOrSession]
    serializer_class = IssueReportSerializer
    queryset = IssueReport.objects.select_related("project", "investigation")
