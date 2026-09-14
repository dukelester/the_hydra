from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.projects.models import Institution, Project, ProjectFollow, ProjectStatus, ProjectView


class ProjectFollowTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Demo Water Office", location="Kisumu")
        self.user = User.objects.create_user(
            username="citizen",
            password="CivicPassphrase-47",
            display_name="Amina Otieno",
        )
        self.project = self._make_project("Community Water Access Project", "Kisumu")

    def _make_project(self, name, county, status=ProjectStatus.IN_PROGRESS, amount="10000000"):
        return Project.objects.create(
            name=name,
            description="A labelled civic project for tests.",
            location=county,
            county=county,
            institution=self.institution,
            allocated_amount=Decimal(amount),
            currency="KES",
            financial_year="2025/2026",
            status=status,
        )

    def test_project_detail_records_authenticated_view(self):
        self.client.force_login(self.user)
        response = self.client.get(self.project.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ProjectView.objects.filter(user=self.user, project=self.project).exists()
        )
        self.assertContains(response, "Track")
        self.assertContains(response, "Favourite")
        self.assertContains(response, "Compare")

    def test_anonymous_recent_views_stay_in_session(self):
        self.client.get(self.project.get_absolute_url())
        self.assertEqual(self.client.session["recent_project_slugs"][0], self.project.slug)

    def test_dashboard_shows_five_recent_views(self):
        self.client.force_login(self.user)
        projects = [
            self._make_project(f"Viewed Project {index}", "Kisumu")
            for index in range(6)
        ]
        now = timezone.now()
        for index, project in enumerate(projects):
            view, _created = ProjectView.objects.update_or_create(user=self.user, project=project)
            ProjectView.objects.filter(pk=view.pk).update(viewed_at=now - timedelta(minutes=index))

        dashboard = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Recently viewed")
        self.assertContains(dashboard, "Viewed Project 0")
        self.assertContains(dashboard, "Viewed Project 4")
        self.assertNotContains(dashboard, "Viewed Project 5")

    def test_track_and_favourite_require_login(self):
        track = self.client.post(reverse("projects:toggle-track", args=[self.project.slug]))
        self.assertEqual(track.status_code, 302)
        self.assertIn(reverse("accounts:login"), track.url)
        favourite = self.client.post(reverse("projects:toggle-favourite", args=[self.project.slug]))
        self.assertEqual(favourite.status_code, 302)
        self.assertIn(reverse("accounts:login"), favourite.url)

    def test_track_and_favourite_toggle(self):
        self.client.force_login(self.user)
        self.client.post(reverse("projects:toggle-track", args=[self.project.slug]))
        follow = ProjectFollow.objects.get(user=self.user, project=self.project)
        self.assertTrue(follow.is_tracked)
        self.assertFalse(follow.is_favourite)

        self.client.post(reverse("projects:toggle-favourite", args=[self.project.slug]))
        follow.refresh_from_db()
        self.assertTrue(follow.is_tracked)
        self.assertTrue(follow.is_favourite)

        self.client.post(reverse("projects:toggle-track", args=[self.project.slug]))
        follow.refresh_from_db()
        self.assertFalse(follow.is_tracked)
        self.assertTrue(follow.is_favourite)

        self.client.post(reverse("projects:toggle-favourite", args=[self.project.slug]))
        self.assertFalse(ProjectFollow.objects.filter(user=self.user, project=self.project).exists())

    def test_dashboard_alerts_when_tracked_project_updates(self):
        self.client.force_login(self.user)
        self.client.post(reverse("projects:toggle-track", args=[self.project.slug]))
        follow = ProjectFollow.objects.get(user=self.user, project=self.project)
        ProjectFollow.objects.filter(pk=follow.pk).update(
            last_seen_updated_at=timezone.now() - timedelta(days=1),
            last_seen_status=ProjectStatus.IN_PROGRESS,
        )
        self.project.status = ProjectStatus.DELAYED
        self.project.save()

        dashboard = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(dashboard, "Record updated")
        self.assertContains(dashboard, "Status changed")
        self.assertContains(dashboard, "In Progress → Delayed")

        self.client.get(self.project.get_absolute_url())
        cleared = self.client.get(reverse("accounts:dashboard"))
        self.assertNotContains(cleared, "Status changed")
        self.assertNotContains(cleared, "Record updated")

    def test_compare_page_projects_and_county_rankings(self):
        nairobi = self._make_project(
            "Nairobi Drain Works",
            "Nairobi",
            status=ProjectStatus.DELAYED,
            amount="50000000",
        )
        self.client.post(reverse("projects:compare-add", args=[self.project.slug]))
        self.client.post(reverse("projects:compare-add", args=[nairobi.slug]))
        response = self.client.get(
            reverse("projects:compare"),
            {"p": [self.project.slug, nairobi.slug], "county": ["Kisumu", "Nairobi"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Community Water Access Project")
        self.assertContains(response, "Nairobi Drain Works")
        self.assertContains(response, "County rankings")
        self.assertContains(response, "Kisumu")
        self.assertContains(response, "Nairobi")
        self.assertContains(response, "Highest recorded budget")
        self.assertContains(response, "County comparison")
        self.assertContains(response, "Clear projects")
        self.assertContains(response, "Build a comparison")
        self.assertContains(response, 'type="checkbox"')
        self.assertContains(response, "Projects (up to")

    def test_compare_url_is_not_a_project_slug(self):
        response = self.client.get(reverse("projects:compare"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compare")
        self.assertContains(response, "County rankings")
        self.assertNotContains(response, 'aria-label="Workspace"')
