from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.projects.models import Institution, Project


class PageTests(TestCase):
    def setUp(self):
        institution = Institution.objects.create(name="Demo Institution", location="Kisumu")
        self.project = Project.objects.create(
            name="Community Water Access Project",
            description="An evidence-first demo project.",
            location="Kisumu",
            county="Kisumu",
            institution=institution,
            allocated_amount=Decimal("35000000"),
            financial_year="2025/2026",
            contractor="Demo Contractor Ltd",
            is_featured=True,
        )

    def test_home_and_project_pages(self):
        home = self.client.get(reverse("core:home"))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, "THEHYDRA")
        self.assertContains(home, "Follow the money. Find the evidence. Take action.")
        self.assertContains(home, "Investigate a Project")

        detail = self.client.get(self.project.get_absolute_url())
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Community Water Access Project")
        self.assertContains(detail, "Follow the money")
        self.assertContains(detail, "Investigate This Project")
        self.assertContains(detail, "Evidence Coverage")
