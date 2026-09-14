from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AccountTests(TestCase):
    def test_register_requires_terms(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newcitizen",
                "password1": "CivicPassphrase-47",
                "password2": "CivicPassphrase-47",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "agree to the terms")
        self.assertFalse(User.objects.filter(username="newcitizen").exists())

    def test_register_succeeds_when_terms_agreed(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newcitizen",
                "password1": "CivicPassphrase-47",
                "password2": "CivicPassphrase-47",
                "agree_to_terms": "on",
            },
        )
        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.assertTrue(User.objects.filter(username="newcitizen").exists())

    def test_dashboard_and_profile_require_login(self):
        dashboard = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(dashboard.status_code, 302)
        profile = self.client.get(reverse("accounts:profile"))
        self.assertEqual(profile.status_code, 302)

    def test_dashboard_and_profile_for_signed_in_user(self):
        user = User.objects.create_user(
            username="citizen",
            password="CivicPassphrase-47",
            display_name="Amina Otieno",
        )
        self.client.force_login(user)
        dashboard = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Amina Otieno")
        self.assertContains(dashboard, "Dashboard")
        self.assertContains(dashboard, "AO")

        saved = self.client.post(
            reverse("accounts:profile"),
            {"display_name": "Amina O.", "email": "amina@example.com"},
        )
        self.assertRedirects(saved, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertEqual(user.display_name, "Amina O.")
        self.assertEqual(user.email, "amina@example.com")

    def test_terms_page(self):
        response = self.client.get(reverse("core:terms"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Terms of use")
