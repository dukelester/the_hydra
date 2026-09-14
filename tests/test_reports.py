from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.investigations.models import Investigation
from apps.projects.models import Institution, Project, ProjectCategory, ProjectStatus
from apps.reports.models import IssueReport, ReportStatus
from apps.reports.services import generate_report_from_investigation


User = get_user_model()


class ReportTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Demo Office", location="Kisumu")
        self.project = Project.objects.create(
            name="Community Water Access Project",
            description="Demo",
            location="Kisumu",
            county="Kisumu",
            institution=self.institution,
            allocated_amount=Decimal("35000000"),
            category=ProjectCategory.WATER,
            financial_year="2025/2026",
            status=ProjectStatus.IN_PROGRESS,
        )
        Project.objects.create(
            name="Nairobi Drain Works",
            description="Demo roads project.",
            location="Nairobi",
            county="Nairobi",
            institution=self.institution,
            allocated_amount=Decimal("50000000"),
            category=ProjectCategory.ROADS,
            financial_year="2025/2026",
            status=ProjectStatus.DELAYED,
        )
        self.user = User.objects.create_user(username="reporter", password="pass12345")
        self.other = User.objects.create_user(username="stranger", password="pass12345")
        self.investigation = Investigation.objects.create(
            project=self.project,
            user=self.user,
            title="Site visit",
            observation="The construction site appears unfinished.",
            location="Kolwa East",
            observed_at=date(2026, 4, 2),
            official_information="Community water project completed.",
            difference_description="Official completion does not match the observed site.",
        )

    def test_structured_report_generation_is_neutral(self):
        report = generate_report_from_investigation(self.investigation, user=self.user)
        self.assertEqual(report.status, ReportStatus.DRAFT)
        self.assertFalse(report.is_public)
        self.assertIn("Potential discrepancy", "Potential discrepancy")
        self.assertIn("require further verification", report.potential_discrepancy.lower())
        self.assertNotIn("corrupt", report.potential_discrepancy.lower())
        self.assertNotIn("fraud", report.potential_discrepancy.lower())
        self.assertIn("Community water project completed.", report.official_information)
        self.assertIn("unfinished", report.citizen_observation)

    def test_report_is_private_to_owner(self):
        report = generate_report_from_investigation(self.investigation, user=self.user)
        self.client.login(username="stranger", password="pass12345")
        denied = self.client.get(report.get_absolute_url())
        self.assertEqual(denied.status_code, 404)

        self.client.login(username="reporter", password="pass12345")
        allowed = self.client.get(report.get_absolute_url())
        self.assertEqual(allowed.status_code, 200)
        self.assertContains(allowed, "Accountability report")
        self.assertContains(allowed, "County file")
        self.assertContains(allowed, "Kisumu")
        self.assertContains(allowed, "Recorded allocation")
        self.assertContains(allowed, "Delivery mix")

    def test_county_report_shows_allocation_and_delivery_charts(self):
        page = self.client.get(reverse("reports:counties"))
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'aria-label="Workspace"')
        self.assertContains(page, "County report")
        self.assertContains(page, "Recorded allocation by county")
        self.assertContains(page, "Kisumu")
        self.assertContains(page, "Nairobi")
        self.assertContains(page, "Allocation by sector")
        self.assertContains(page, "Water")
        self.assertContains(page, "Roads")
        self.assertContains(page, "Highest delayed share")

        filtered = self.client.get(reverse("reports:counties"), {"county": "Kisumu"})
        self.assertContains(filtered, "County file")
        self.assertContains(filtered, "Kisumu")
        self.assertContains(filtered, "Delivery mix")
        self.assertContains(filtered, "Allocation by sector")

    def test_save_report_from_review_form(self):
        report = generate_report_from_investigation(self.investigation, user=self.user)
        self.client.login(username="reporter", password="pass12345")
        response = self.client.post(
            reverse("reports:detail", kwargs={"pk": report.pk}),
            {
                "title": report.title,
                "official_information": report.official_information,
                "citizen_observation": report.citizen_observation,
                "evidence_summary": report.evidence_summary,
                "potential_discrepancy": report.potential_discrepancy,
                "recommended_next_steps": report.recommended_next_steps,
                "status": ReportStatus.SUBMITTED,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)
        self.assertFalse(report.is_public)
