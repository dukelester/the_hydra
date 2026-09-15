from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.projects.models import Institution, Project, ProjectStatus, TimelineEvent, TimelineStage
from apps.sources.models import Evidence, EvidenceVerificationStatus, SourceDocument
from apps.core.services.coverage import calculate_evidence_coverage
from apps.core.services.timeline import build_project_timeline


User = get_user_model()


class ProjectModelTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Demo Water Office",
            description="Test institution",
            location="Kisumu",
        )
        self.project = Project.objects.create(
            name="Community Water Access Project",
            description="A test water project",
            location="Kisumu",
            county="Kisumu",
            institution=self.institution,
            allocated_amount=Decimal("35000000"),
            currency="KES",
            financial_year="2025/2026",
            status=ProjectStatus.IN_PROGRESS,
        )

    def test_project_creation_and_slug(self):
        self.assertEqual(self.project.slug, "community-water-access-project")
        self.assertEqual(self.project.format_amount(), "KSh 35,000,000")
        self.assertEqual(self.project.institution.name, "Demo Water Office")

    def test_institution_relationship(self):
        self.assertEqual(self.institution.projects.count(), 1)
        self.assertEqual(self.institution.projects.first(), self.project)

    def test_evidence_relationship_and_status(self):
        document = SourceDocument.objects.create(
            title="2025/26 County Development Budget",
            publisher="Demo Treasury",
        )
        evidence = Evidence.objects.create(
            project=self.project,
            claim="Project allocation is KSh 35 million.",
            evidence_text="Listed as KSh 35,000,000.",
            source_document=document,
            page_number=42,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        self.assertEqual(self.project.evidence_items.count(), 1)
        self.assertEqual(evidence.source_document.title, "2025/26 County Development Budget")
        self.assertEqual(evidence.verification_status, EvidenceVerificationStatus.VERIFIED)

    def test_timeline_generation_marks_missing_evidence(self):
        document = SourceDocument.objects.create(title="Budget", publisher="Demo")
        evidence = Evidence.objects.create(
            project=self.project,
            claim="Allocated",
            evidence_text="35M",
            source_document=document,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        TimelineEvent.objects.create(
            project=self.project,
            stage=TimelineStage.ALLOCATION,
            title="KSh 35M",
            evidence=evidence,
            sort_order=1,
        )
        timeline = build_project_timeline(self.project)
        self.assertEqual(len(timeline), 6)
        allocation = timeline[0]
        self.assertTrue(allocation["has_evidence"])
        self.assertFalse(allocation["evidence_unavailable"])
        procurement = next(item for item in timeline if item["stage"] == TimelineStage.PROCUREMENT)
        self.assertTrue(procurement["evidence_unavailable"])

    def test_evidence_coverage(self):
        Evidence.objects.create(
            project=self.project,
            claim="A",
            evidence_text="yes",
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        Evidence.objects.create(
            project=self.project,
            claim="B",
            verification_status=EvidenceVerificationStatus.UNKNOWN,
        )
        coverage = calculate_evidence_coverage(self.project)
        self.assertEqual(coverage["total_claims"], 2)
        self.assertEqual(coverage["supported"], 1)
        self.assertEqual(coverage["percent"], 50)
        self.assertTrue(any("Evidence unavailable" in item or "unknown" in item.lower() or "lacks" in item.lower() for item in coverage["missing"]))

    def test_institution_pages(self):
        listing = self.client.get(reverse("institutions:list"))
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, "Institutions")
        self.assertContains(listing, "Demo Water Office")
        self.assertContains(listing, "1 project")

        filtered = self.client.get(reverse("institutions:list"), {"q": "Water"})
        self.assertContains(filtered, "Demo Water Office")
        empty = self.client.get(reverse("institutions:list"), {"q": "NoSuchBody"})
        self.assertContains(empty, "No institutions match these filters.")

        detail = self.client.get(self.institution.get_absolute_url())
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Demo Water Office")
        self.assertContains(detail, "Institution facts")
        self.assertContains(detail, "Related projects")
        self.assertContains(detail, "Community Water Access Project")
        self.assertContains(detail, str(self.institution.pk))

    def test_project_list_filter_follows_user_country(self):
        Project.objects.create(
            name="[DEMO] Mukaza Public Standpipe Rehabilitation",
            description="A Burundi file.",
            location="Mukaza",
            country="BI",
            county="Bujumbura",
            institution=self.institution,
        )
        guest = self.client.get(reverse("projects:list"))
        self.assertContains(guest, "Community Water Access Project")
        self.assertContains(guest, ">County<")
        self.assertContains(guest, "Kisumu")
        self.assertNotContains(guest, "Bujumbura")
        self.assertNotContains(guest, "Mukaza Public Standpipe")

        user = User.objects.create_user(username="bujumbura", password="pass12345", country="BI")
        self.client.login(username="bujumbura", password="pass12345")
        page = self.client.get(reverse("projects:list"))
        self.assertContains(page, "Mukaza Public Standpipe")
        self.assertContains(page, ">Province<")
        self.assertContains(page, "Bujumbura")
        self.assertNotContains(page, "Community Water Access Project")
        self.assertNotContains(page, ">Kisumu<")
