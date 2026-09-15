from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.investigations.models import Investigation, InvestigationVerificationStatus
from apps.projects.models import Institution, Project
from apps.reports.models import IssueReport, ReportStatus
from apps.reports.services import generate_report_from_investigation


User = get_user_model()


class StaffDashboardTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="County Works", location="Kisumu")
        self.project = Project.objects.create(
            name="Community Water Access Project",
            description="Demo",
            location="Kisumu",
            county="Kisumu",
            institution=self.institution,
            allocated_amount=Decimal("1000000"),
        )
        self.staff = User.objects.create_user(
            username="clerk",
            password="CivicPassphrase-47",
            is_staff=True,
        )
        self.citizen = User.objects.create_user(username="resident", password="CivicPassphrase-47")

    def test_staff_dashboard_requires_staff(self):
        url = reverse("staff:dashboard")
        guest = self.client.get(url)
        self.assertEqual(guest.status_code, 302)

        self.client.force_login(self.citizen)
        forbidden = self.client.get(url)
        self.assertEqual(forbidden.status_code, 403)

        self.client.force_login(self.staff)
        allowed = self.client.get(url)
        self.assertEqual(allowed.status_code, 200)
        self.assertContains(allowed, "Admin dashboard")
        self.assertContains(allowed, "Projects")
        self.assertContains(allowed, "Investigations to review")

    def test_staff_can_create_and_edit_a_project(self):
        self.client.force_login(self.staff)
        created = self.client.post(
            reverse("staff:project-create"),
            {
                "name": "Ward Clinic Upgrade",
                "description": "Recorded clinic works.",
                "category": "health",
                "location": "Kisumu",
                "county": "Kisumu",
                "institution": self.institution.pk,
                "currency": "KES",
                "status": "planned",
            },
        )
        self.assertEqual(created.status_code, 302)
        project = Project.objects.get(name="Ward Clinic Upgrade")
        self.assertTrue(project.slug)

        edited = self.client.post(
            reverse("staff:project-edit", args=[project.pk]),
            {
                "name": "Ward Clinic Upgrade",
                "description": "Recorded clinic works.",
                "category": "health",
                "location": "Kisumu",
                "county": "Kisumu",
                "institution": self.institution.pk,
                "currency": "KES",
                "status": "in_progress",
            },
        )
        self.assertEqual(edited.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.status, "in_progress")

    def test_staff_can_review_investigation_and_publish_report(self):
        investigation = Investigation.objects.create(
            project=self.project,
            user=self.citizen,
            title="Unfinished site",
            observation="Works incomplete",
            location="Kisumu",
            observed_at=date(2026, 4, 2),
            official_information="Completed",
            difference_description="Mismatch",
        )
        report = generate_report_from_investigation(investigation, user=self.citizen)
        self.client.force_login(self.staff)

        reviewed = self.client.post(
            reverse("staff:investigation-edit", args=[investigation.pk]),
            {
                "project": self.project.pk,
                "title": "Unfinished site",
                "observation": "Works incomplete",
                "location": "Kisumu",
                "observed_at": "2026-04-02",
                "official_information": "Completed",
                "difference_description": "Mismatch",
                "verification_status": InvestigationVerificationStatus.UNDER_REVIEW,
            },
        )
        self.assertEqual(reviewed.status_code, 302)
        investigation.refresh_from_db()
        self.assertEqual(investigation.verification_status, InvestigationVerificationStatus.UNDER_REVIEW)

        published = self.client.post(
            reverse("staff:report-edit", args=[report.pk]),
            {
                "title": report.title,
                "official_information": report.official_information,
                "citizen_observation": report.citizen_observation,
                "evidence_summary": report.evidence_summary,
                "potential_discrepancy": report.potential_discrepancy,
                "recommended_next_steps": report.recommended_next_steps,
                "status": ReportStatus.UNDER_REVIEW,
                "is_public": "on",
            },
        )
        self.assertEqual(published.status_code, 302)
        report.refresh_from_db()
        self.assertTrue(report.is_public)
        self.assertEqual(report.status, ReportStatus.UNDER_REVIEW)
