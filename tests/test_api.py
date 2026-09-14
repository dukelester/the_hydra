from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.investigations.models import Investigation
from apps.projects.models import Institution, Project, TimelineEvent, TimelineStage
from apps.sources.models import Evidence, EvidenceVerificationStatus


User = get_user_model()


class APITests(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.institution = Institution.objects.create(name="API Office", location="Kisumu")
        self.project = Project.objects.create(
            name="API Water Project",
            description="API demo",
            location="Kisumu",
            county="Kisumu",
            institution=self.institution,
            allocated_amount=Decimal("1000000"),
        )
        Evidence.objects.create(
            project=self.project,
            claim="Allocation is KSh 1 million.",
            evidence_text="Recorded in demo data.",
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        TimelineEvent.objects.create(
            project=self.project,
            stage=TimelineStage.ALLOCATION,
            title="KSh 1M",
            sort_order=1,
        )
        self.user = User.objects.create_user(username="apiuser", password="pass12345")

    def test_project_list_and_detail(self):
        list_response = self.api.get("/api/v1/projects/")
        self.assertEqual(list_response.status_code, 200)
        self.assertGreaterEqual(list_response.data["count"], 1)

        detail = self.api.get(f"/api/v1/projects/{self.project.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["name"], "API Water Project")
        self.assertIn("evidence_coverage", detail.data)
        self.assertIn("timeline", detail.data)

    def test_evidence_and_timeline_endpoints(self):
        evidence = self.api.get(f"/api/v1/projects/{self.project.pk}/evidence/")
        self.assertEqual(evidence.status_code, 200)
        self.assertGreaterEqual(evidence.data["count"], 1)

        timeline = self.api.get(f"/api/v1/projects/{self.project.pk}/timeline/")
        self.assertEqual(timeline.status_code, 200)
        self.assertEqual(len(timeline.data["timeline"]), 6)
        self.assertTrue(any(item["evidence_unavailable"] for item in timeline.data["timeline"]))

    def test_institutions_policies_and_search(self):
        self.assertEqual(self.api.get("/api/v1/institutions/").status_code, 200)
        self.assertEqual(self.api.get("/api/v1/policies/").status_code, 200)
        search = self.api.get("/api/v1/search/", {"q": "API Water"})
        self.assertEqual(search.status_code, 200)
        self.assertGreaterEqual(search.data["total"], 1)

    def test_investigation_and_report_flow_and_authorization(self):
        created = self.api.post(
            "/api/v1/investigations/",
            {
                "project_id": self.project.pk,
                "observation": "Site unfinished",
                "location": "Kisumu",
                "observed_at": "2026-04-02",
                "official_information": "Project completed",
                "difference_description": "Mismatch between record and site",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        investigation_id = created.data["id"]

        visible = self.api.get(f"/api/v1/investigations/{investigation_id}/")
        self.assertEqual(visible.status_code, 200)

        report = self.api.post(
            "/api/v1/reports/",
            {"investigation_id": investigation_id},
            format="json",
        )
        self.assertEqual(report.status_code, 201)
        report_id = report.data["id"]
        self.assertFalse(report.data["is_public"])

        other = APIClient()
        other.force_authenticate(user=self.user)
        hidden_inv = other.get(f"/api/v1/investigations/{investigation_id}/")
        self.assertIn(hidden_inv.status_code, {403, 404})
        hidden_report = other.get(f"/api/v1/reports/{report_id}/")
        self.assertIn(hidden_report.status_code, {403, 404})
