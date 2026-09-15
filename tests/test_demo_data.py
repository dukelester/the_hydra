from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.core.management.commands.load_demo_data import DEMO_USER_PASSWORD, DEMO_USER_USERNAME
from apps.projects.models import Project
from apps.sources.models import SourceDocument

User = get_user_model()


class DemoDataTests(TestCase):
    def test_load_demo_data_covers_five_countries(self):
        call_command("load_demo_data", reset=True)
        demo = Project.objects.filter(is_demo=True)
        self.assertGreaterEqual(demo.count(), 20)
        self.assertEqual(
            set(demo.values_list("country", flat=True)),
            {"KE", "TZ", "BI", "CD", "NG"},
        )
        expected = {
            "KE": ("KES", "Kisumu"),
            "TZ": ("TZS", "Dar es Salaam"),
            "BI": ("BIF", "Bujumbura"),
            "CD": ("CDF", "Kinshasa"),
            "NG": ("NGN", "Lagos"),
        }
        for code, (currency, county) in expected.items():
            qs = demo.filter(country=code)
            self.assertGreaterEqual(qs.count(), 3, code)
            self.assertTrue(qs.filter(name__contains="[DEMO]").exists(), code)
            self.assertTrue(qs.filter(currency=currency).exists(), code)
            self.assertTrue(qs.filter(county=county).exists(), code)
            self.assertTrue(qs.filter(is_featured=True).exists(), code)
        self.assertTrue(SourceDocument.objects.filter(is_demo=True, title__contains="[DEMO]").exists())
        self.assertFalse(demo.filter(description__icontains="corruption").exists())

    def test_load_demo_data_creates_sign_in_user(self):
        call_command("load_demo_data", reset=True)
        user = User.objects.get(username=DEMO_USER_USERNAME)
        self.assertTrue(user.check_password(DEMO_USER_PASSWORD))
        self.assertEqual(user.email, "demo@thehydra.local")
        self.assertEqual(user.display_name, "Amina Otieno")
        self.assertEqual(user.role, UserRole.CITIZEN)
        self.assertEqual(user.country, "KE")
        self.assertEqual(user.county, "Kisumu")
        self.assertEqual(user.constituency, "Kisumu East")
        self.assertEqual(user.ward, "Kolwa East")
        self.assertFalse(user.is_staff)
        self.assertTrue(user.area_watches.filter(county="Kisumu", constituency="Kisumu East").exists())
        self.assertTrue(
            user.project_follows.filter(
                project__slug="community-water-access-project",
                is_tracked=True,
                is_favourite=True,
            ).exists()
        )
        logged_in = self.client.login(username=DEMO_USER_USERNAME, password=DEMO_USER_PASSWORD)
        self.assertTrue(logged_in)
        dashboard = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Amina Otieno")
        self.assertContains(dashboard, "Community Water Access")
