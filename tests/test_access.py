from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.investigations.models import Investigation
from apps.projects.models import Institution, Project


User = get_user_model()


class AccessConstraintTests(TestCase):
    def setUp(self):
        institution = Institution.objects.create(name="Kisumu Water Office", location="Kisumu")
        self.project = Project.objects.create(
            name="Community Water Access Project",
            description="An evidence-first demo project.",
            location="Kisumu",
            county="Kisumu",
            institution=institution,
            allocated_amount=Decimal("35000000"),
            financial_year="2025/2026",
        )
        self.user = User.objects.create_user(username="observer", password="pass12345")

    def test_privacy_page(self):
        response = self.client.get(reverse("core:privacy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Privacy")
        self.assertContains(response, "Guest observations are stored as anonymous")
        self.assertContains(response, "Kiswahili")

    def test_project_lists_kenya_next_steps(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "What you can do next")
        self.assertContains(response, "Access to Information Act")
        self.assertContains(response, "Commission on Administrative Justice")
        self.assertContains(response, "Kisumu Water Office")
        self.assertContains(response, "Investigate This Project")
        self.assertContains(response, "rules recorded for Kenya")

    def test_tanzania_project_uses_local_next_steps(self):
        institution = Institution.objects.create(name="Ilala Municipal Council", location="Dar es Salaam")
        project = Project.objects.create(
            name="Ilala Water Network",
            description="A Tanzania file.",
            location="Ilala",
            country="TZ",
            county="Dar es Salaam",
            institution=institution,
        )
        response = self.client.get(project.get_absolute_url())
        self.assertContains(response, "Commission for Human Rights and Good Governance")
        self.assertContains(response, "rules recorded for Tanzania")
        self.assertContains(response, "Region: Dar es Salaam")
        self.assertNotContains(response, "Commission on Administrative Justice")

    def test_burundi_project_uses_local_next_steps(self):
        institution = Institution.objects.create(name="Bujumbura Water Service Desk", location="Bujumbura")
        project = Project.objects.create(
            name="Mukaza Public Standpipe Rehabilitation",
            description="A Burundi file.",
            location="Mukaza",
            country="BI",
            county="Bujumbura",
            institution=institution,
        )
        response = self.client.get(project.get_absolute_url())
        self.assertContains(response, "Médiateur de la République")
        self.assertContains(response, "rules recorded for Burundi")
        self.assertContains(response, "Province: Bujumbura")
        self.assertNotContains(response, "Access to Information Act")

    def test_lite_mode_skips_webfonts_and_live_search(self):
        toggle = self.client.post(
            reverse("core:lite"),
            {"lite": "1", "next": "/"},
            follow=True,
        )
        self.assertEqual(toggle.status_code, 200)
        self.assertNotContains(toggle, "fonts.googleapis.com")
        self.assertNotContains(toggle, "htmx.min.js")
        self.assertContains(toggle, "Use full pages")

        restored = self.client.post(
            reverse("core:lite"),
            {"lite": "0", "next": "/"},
            follow=True,
        )
        self.assertContains(restored, "fonts.googleapis.com")
        self.assertContains(restored, "Use less data")

    def test_save_data_header_enables_lite(self):
        response = self.client.get("/", headers={"Save-Data": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "fonts.googleapis.com")

    def test_arabic_uses_rtl(self):
        response = self.client.post("/i18n/setlang/", {"language": "ar", "next": "/"})
        self.assertEqual(response.status_code, 302)
        home = self.client.get("/")
        self.assertContains(home, 'lang="ar"')
        self.assertContains(home, 'dir="rtl"')
        self.assertContains(home, "المشاريع")

    def test_language_changes_without_apply(self):
        home = self.client.get("/")
        self.assertContains(home, "Kiswahili")
        self.assertContains(home, 'name="language"')
        self.assertNotContains(home, ">Apply<")
        self.assertNotContains(home, 'id="language-select"')

    def test_offline_shell_and_service_worker(self):
        offline = self.client.get(reverse("core:offline"))
        self.assertEqual(offline.status_code, 200)
        self.assertContains(offline, "You are offline")
        worker = self.client.get(reverse("core:service-worker"))
        self.assertEqual(worker.status_code, 200)
        self.assertEqual(worker["Content-Type"].split(";")[0], "application/javascript")
        self.assertEqual(worker["Service-Worker-Allowed"], "/")
        self.assertContains(worker, "hydra-pages-v1")
        self.assertContains(worker, "/offline/")

    def test_swahili_translates_chrome(self):
        self.client.post("/i18n/setlang/", {"language": "sw", "next": "/"})
        home = self.client.get("/")
        self.assertContains(home, 'lang="sw"')
        self.assertContains(home, "Miradi")
        self.assertContains(home, "Fuata pesa")

    def test_signed_in_user_can_hide_account_name(self):
        self.client.login(username="observer", password="pass12345")
        url = reverse("projects:investigate", kwargs={"slug": self.project.slug})
        page = self.client.get(url)
        self.assertContains(page, "Do not show my account name")
        self.assertContains(page, "What you can do next")
        self.client.post(
            url,
            {
                "observation": "The site looks unfinished.",
                "location": "Kisumu",
                "observed_at": "2026-04-02",
                "official_information": "Recorded as completed.",
                "difference_description": "The site does not look complete.",
                "hide_account": "on",
            },
        )
        investigation = Investigation.objects.get()
        self.assertEqual(investigation.user, self.user)
        self.assertTrue(investigation.is_anonymous)
