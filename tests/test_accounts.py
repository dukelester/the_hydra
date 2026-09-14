from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.models import User, UserRole


class AccountTests(TestCase):
    def test_register_is_two_steps(self):
        first = self.client.get(reverse("accounts:register"))
        self.assertEqual(first.status_code, 200)
        self.assertContains(first, "Create an account")
        self.assertContains(first, "Continue")
        self.assertContains(first, "Your name")
        self.assertNotContains(first, "Create a password")
        self.assertNotContains(first, "I agree to the")

        step1 = self.client.post(
            reverse("accounts:register"),
            {"step": "1", "username": "newcitizen", "display_name": "Amina"},
        )
        self.assertEqual(step1.status_code, 200)
        self.assertContains(step1, "Create a password")
        self.assertContains(step1, "@newcitizen")
        self.assertContains(step1, "Amina")
        self.assertContains(step1, "I agree to the")
        self.assertNotContains(step1, "Choose a username")
        self.assertFalse(User.objects.filter(username="newcitizen").exists())

    def test_register_requires_terms(self):
        self.client.post(
            reverse("accounts:register"),
            {"step": "1", "username": "newcitizen", "display_name": ""},
        )
        response = self.client.post(
            reverse("accounts:register"),
            {
                "step": "2",
                "password1": "CivicPassphrase-47",
                "password2": "CivicPassphrase-47",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "agree to the terms")
        self.assertFalse(User.objects.filter(username="newcitizen").exists())

    def test_register_succeeds_when_terms_agreed(self):
        self.client.post(
            reverse("accounts:register"),
            {"step": "1", "username": "newcitizen", "display_name": "Amina"},
        )
        response = self.client.post(
            reverse("accounts:register"),
            {
                "step": "2",
                "password1": "CivicPassphrase-47",
                "password2": "CivicPassphrase-47",
                "agree_to_terms": "on",
            },
        )
        self.assertRedirects(response, reverse("accounts:dashboard"))
        user = User.objects.get(username="newcitizen")
        self.assertEqual(user.display_name, "Amina")

    def test_register_back_returns_to_name_step(self):
        self.client.post(
            reverse("accounts:register"),
            {"step": "1", "username": "newcitizen", "display_name": "Amina"},
        )
        back = self.client.post(
            reverse("accounts:register"),
            {"step": "2", "intent": "back"},
        )
        self.assertEqual(back.status_code, 200)
        self.assertContains(back, "Continue")
        self.assertContains(back, "newcitizen")
        self.assertContains(back, "Amina")

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
            {
                "display_name": "Amina O.",
                "email": "amina@example.com",
                "first_name": "Amina",
                "last_name": "Otieno",
                "affiliation": "Kisumu Civic Desk",
                "role": UserRole.JOURNALIST,
                "county": "Kisumu",
                "location": "Nyalenda",
                "website": "https://example.com",
                "bio": "I follow county water projects.",
            },
        )
        self.assertRedirects(saved, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertEqual(user.display_name, "Amina O.")
        self.assertEqual(user.email, "amina@example.com")
        self.assertEqual(user.first_name, "Amina")
        self.assertEqual(user.affiliation, "Kisumu Civic Desk")
        self.assertEqual(user.role, UserRole.JOURNALIST)
        self.assertEqual(user.county, "Kisumu")
        self.assertEqual(user.location, "Nyalenda")
        self.assertEqual(user.website, "https://example.com")
        self.assertEqual(user.bio, "I follow county water projects.")

        profile = self.client.get(reverse("accounts:profile"))
        self.assertContains(profile, "Change password")
        self.assertContains(profile, "About you")

    def test_profile_fields_can_stay_blank(self):
        user = User.objects.create_user(username="citizen", password="CivicPassphrase-47")
        self.client.force_login(user)
        saved = self.client.post(reverse("accounts:profile"), {})
        self.assertRedirects(saved, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertEqual(user.display_name, "")
        self.assertEqual(user.email, "")
        self.assertEqual(user.role, "")
        self.assertEqual(user.bio, "")

    def test_password_reset_sends_email_and_sets_new_password(self):
        user = User.objects.create_user(
            username="citizen",
            password="CivicPassphrase-47",
            email="amina@example.com",
        )
        request_page = self.client.get(reverse("accounts:password-reset"))
        self.assertEqual(request_page.status_code, 200)
        self.assertContains(request_page, "Reset your password")

        sent = self.client.post(
            reverse("accounts:password-reset"),
            {"email": "amina@example.com"},
        )
        self.assertRedirects(sent, reverse("accounts:password-reset-done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset your H.Y.D.R.A. password", mail.outbox[0].subject)
        self.assertIn("password-reset/", mail.outbox[0].body)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": uid, "token": token},
        )
        confirm = self.client.get(confirm_url)
        self.assertEqual(confirm.status_code, 302)
        saved = self.client.post(
            confirm.url,
            {
                "new_password1": "NewCivicPassphrase-99",
                "new_password2": "NewCivicPassphrase-99",
            },
        )
        self.assertRedirects(saved, reverse("accounts:password-reset-complete"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewCivicPassphrase-99"))

        login = self.client.post(
            reverse("accounts:login"),
            {"username": "citizen", "password": "NewCivicPassphrase-99"},
        )
        self.assertRedirects(login, reverse("accounts:dashboard"))

    def test_password_reset_does_not_reveal_unknown_email(self):
        response = self.client.post(
            reverse("accounts:password-reset"),
            {"email": "nobody@example.com"},
        )
        self.assertRedirects(response, reverse("accounts:password-reset-done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_password_change_for_signed_in_user(self):
        user = User.objects.create_user(
            username="citizen",
            password="CivicPassphrase-47",
        )
        self.client.force_login(user)
        page = self.client.get(reverse("accounts:password-change"))
        self.assertEqual(page.status_code, 200)
        saved = self.client.post(
            reverse("accounts:password-change"),
            {
                "old_password": "CivicPassphrase-47",
                "new_password1": "NewCivicPassphrase-99",
                "new_password2": "NewCivicPassphrase-99",
            },
        )
        self.assertRedirects(saved, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewCivicPassphrase-99"))

    def test_terms_page(self):
        response = self.client.get(reverse("core:terms"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Terms of use")
