from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.projects.models import Institution, Project, ProjectStatus


class AreaWatchTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Demo Water Office", location="Kisumu")
        self.user = User.objects.create_user(
            username="citizen",
            password="CivicPassphrase-47",
            display_name="Amina Otieno",
        )
        self.kisumu = Project.objects.create(
            name="Community Water Access Project",
            description="A labelled civic project for tests.",
            location="Kolwa East",
            county="Kisumu",
            constituency="Kisumu East",
            ward="Kolwa East",
            institution=self.institution,
            status=ProjectStatus.IN_PROGRESS,
        )
        self.central = Project.objects.create(
            name="Solid Waste Collection Upgrade",
            description="Another Kisumu project.",
            location="Market Milimani",
            county="Kisumu",
            constituency="Kisumu Central",
            ward="Market Milimani",
            institution=self.institution,
            status=ProjectStatus.PLANNED,
        )
        Project.objects.create(
            name="Nairobi Drain Works",
            description="A Nairobi project.",
            location="Nairobi",
            county="Nairobi",
            institution=self.institution,
            status=ProjectStatus.DELAYED,
        )

    def test_my_county_requires_login(self):
        response = self.client.get(reverse("accounts:my-county"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_track_county_shows_matching_projects(self):
        self.client.force_login(self.user)
        page = self.client.get(reverse("accounts:my-county"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Track my county")

        saved = self.client.post(
            reverse("accounts:my-county"),
            {"county": "Kisumu", "constituency": "", "ward": ""},
        )
        self.assertRedirects(saved, reverse("accounts:my-county"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.track_area)
        self.assertEqual(self.user.county, "Kisumu")

        feed = self.client.get(reverse("accounts:my-county"))
        self.assertContains(feed, "Community Water Access Project")
        self.assertContains(feed, "Solid Waste Collection Upgrade")
        self.assertNotContains(feed, "Nairobi Drain Works")
        self.assertContains(feed, "Kisumu")

        dashboard = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(dashboard, "My county")
        self.assertContains(dashboard, "Watching Kisumu")

    def test_constituency_narrows_the_feed(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("accounts:my-county"),
            {"county": "Kisumu", "constituency": "Kisumu East", "ward": "Kolwa East"},
        )
        feed = self.client.get(reverse("accounts:my-county"))
        self.assertContains(feed, "Community Water Access Project")
        self.assertNotContains(feed, "Solid Waste Collection Upgrade")
        self.user.refresh_from_db()
        self.assertEqual(self.user.area_label(), "Kisumu · Kisumu East · Kolwa East")

    def test_stop_tracking_hides_the_feed(self):
        self.client.force_login(self.user)
        self.client.post(reverse("accounts:my-county"), {"county": "Kisumu"})
        stopped = self.client.post(reverse("accounts:my-county"), {"intent": "stop"})
        self.assertRedirects(stopped, reverse("accounts:my-county"))
        self.user.refresh_from_db()
        self.assertFalse(self.user.track_area)
        self.assertEqual(self.user.county, "Kisumu")
        feed = self.client.get(reverse("accounts:my-county"))
        self.assertContains(feed, "Choose a county to start the feed")
        self.assertNotContains(feed, "Community Water Access Project")
