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
        self.assertContains(dashboard, "My areas")
        self.assertContains(dashboard, "Watching Kisumu")
        self.assertTrue(self.user.area_watches.filter(county="Kisumu").exists())

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

    def test_area_options_require_login(self):
        guest = self.client.get(reverse("accounts:area-options"), {"county": "Kisumu"})
        self.assertEqual(guest.status_code, 302)
        self.assertIn(reverse("accounts:login"), guest.url)

    def test_area_options_follow_the_selected_county(self):
        self.client.force_login(self.user)
        county = self.client.get(
            reverse("accounts:area-options"),
            {"county": "Kajiado"},
            HTTP_HX_TRIGGER_NAME="county",
        )
        self.assertEqual(county.status_code, 200)
        self.assertContains(county, "Kajiado North")
        self.assertContains(county, "Kajiado Central")
        self.assertNotContains(county, "Kisumu East")
        self.assertNotContains(county, "Funyula")

        wards = self.client.get(
            reverse("accounts:area-options"),
            {"county": "Kisumu", "constituency": "Kisumu East"},
            HTTP_HX_TRIGGER_NAME="constituency",
        )
        self.assertContains(wards, "Kolwa East")
        self.assertContains(wards, "Kajulu")
        self.assertNotContains(wards, "Market Milimani")
        self.assertNotContains(wards, "Port Reitz")

    def test_mismatched_constituency_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:my-county"),
            {"county": "Kajiado", "constituency": "Kisumu East", "ward": "Funyula"},
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.track_area)
        self.assertFalse(self.user.area_watches.exists())
        self.assertContains(response, "valid choice")

    def test_user_can_track_up_to_four_areas(self):
        self.client.force_login(self.user)
        self.client.post(reverse("accounts:my-county"), {"county": "Kisumu"})
        self.client.post(reverse("accounts:my-county"), {"county": "Nairobi"})
        feed = self.client.get(reverse("accounts:my-county"))
        self.assertContains(feed, "Community Water Access Project")
        self.assertContains(feed, "Nairobi Drain Works")
        self.assertContains(feed, "2 of 4 areas")
        self.user.refresh_from_db()
        self.assertEqual(self.user.area_watches.count(), 2)
        self.assertEqual(self.user.area_label(), "Kisumu; Nairobi")

        dashboard = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(dashboard, "2 areas")

        for county in ("Kajiado", "Mombasa"):
            self.client.post(reverse("accounts:my-county"), {"county": county})
        self.user.refresh_from_db()
        self.assertEqual(self.user.area_watches.count(), 4)

        blocked = self.client.post(reverse("accounts:my-county"), {"county": "Nakuru"})
        self.assertEqual(blocked.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.area_watches.count(), 4)
        self.assertContains(blocked, "You are tracking 4 areas")

        first = self.user.area_watches.get(county="Kisumu")
        removed = self.client.post(reverse("accounts:my-county"), {"remove": str(first.pk)})
        self.assertRedirects(removed, reverse("accounts:my-county"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.area_watches.count(), 3)
        self.assertFalse(self.user.area_watches.filter(county="Kisumu").exists())
