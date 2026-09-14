from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.investigations.models import Investigation
from apps.projects.models import Institution, Project


User = get_user_model()


def png_file(name="site.png"):
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color=(20, 80, 40)).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class InvestigationTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Demo Office", location="Kisumu")
        self.project = Project.objects.create(
            name="Community Water Access Project",
            description="Demo",
            location="Kisumu",
            county="Kisumu",
            institution=self.institution,
            allocated_amount=Decimal("35000000"),
            status="completed",
        )
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="other", password="pass12345")

    def _payload(self, **overrides):
        data = {
            "observation": "The construction site appears unfinished.",
            "location": "Kolwa East",
            "observed_at": "2026-04-02",
            "official_information": "Community water project completed.",
            "difference_description": "Official records say completed; the site still looks unfinished.",
            "evidence_description": "Photograph of the unfinished works.",
        }
        data.update(overrides)
        return data

    def test_investigate_page_shows_project_context(self):
        url = reverse("projects:investigate", kwargs={"slug": self.project.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Investigate this project")
        self.assertContains(response, "Community Water Access Project")
        self.assertContains(response, "What you saw")
        self.assertContains(response, "Compare the record")
        self.assertContains(response, "Supporting evidence")
        self.assertContains(response, "Review evidence first")
        self.assertContains(response, "Citizen observation")

    def test_anonymous_investigation_submission_with_file(self):
        url = reverse("projects:investigate", kwargs={"slug": self.project.slug})
        response = self.client.post(url, {**self._payload(), "attachment": png_file()}, follow=True)
        self.assertEqual(response.status_code, 200)
        investigation = Investigation.objects.get()
        self.assertTrue(investigation.is_anonymous)
        self.assertIsNone(investigation.user)
        self.assertTrue(investigation.attachment)
        self.assertContains(response, "Citizen observation")
        self.assertContains(response, "Official information")

    def test_owner_can_view_and_other_user_cannot(self):
        investigation = Investigation.objects.create(
            project=self.project,
            user=self.owner,
            title="Owner observation",
            observation="Unfinished",
            location="Kisumu",
            observed_at=date(2026, 4, 2),
            official_information="Completed",
            difference_description="Mismatch",
        )
        self.client.login(username="owner", password="pass12345")
        allowed = self.client.get(investigation.get_absolute_url())
        self.assertEqual(allowed.status_code, 200)

        self.client.login(username="other", password="pass12345")
        denied = self.client.get(investigation.get_absolute_url())
        self.assertEqual(denied.status_code, 404)
