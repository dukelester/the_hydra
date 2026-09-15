from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.core.governance import request_country
from apps.core.services.coverage import calculate_evidence_coverage
from apps.core.services.timeline import build_project_timeline
from apps.projects.models import Institution, Project
from apps.projects.serializers import (
    EvidenceSerializer,
    InstitutionSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
)
from apps.sources.models import Evidence
from rest_framework.response import Response
from rest_framework.views import APIView


class ProjectListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProjectListSerializer
    queryset = Project.objects.select_related("institution").prefetch_related("evidence_items")

    def get_queryset(self):
        qs = super().get_queryset().filter(country=request_country(self.request))
        q = self.request.query_params.get("q")
        county = self.request.query_params.get("county")
        if q:
            qs = qs.filter(name__icontains=q)
        if county:
            qs = qs.filter(county__iexact=county)
        return qs


class ProjectDetailAPIView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProjectDetailSerializer
    queryset = Project.objects.select_related("institution").prefetch_related(
        "allocations__source_document",
        "source_documents",
        "evidence_items__source_document",
        "timeline_events__evidence",
    )


class ProjectEvidenceAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = EvidenceSerializer

    def get_queryset(self):
        return Evidence.objects.filter(project_id=self.kwargs["pk"]).select_related("source_document")


class ProjectTimelineAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        project = Project.objects.prefetch_related("timeline_events__evidence").filter(pk=pk).first()
        if not project:
            return Response({"detail": "Not found."}, status=404)
        payload = []
        for item in build_project_timeline(project):
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
                    "occurred_on": event.occurred_on.isoformat() if event and event.occurred_on else None,
                }
            )
        coverage = calculate_evidence_coverage(project)
        return Response({"timeline": payload, "evidence_coverage": coverage["percent"]})


class InstitutionListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = InstitutionSerializer
    queryset = Institution.objects.all()
