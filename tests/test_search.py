from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.core.services.search import search_civic_data
from apps.policies.models import Policy
from apps.projects.models import Institution, Project
from apps.sources.models import SourceDocument


class SearchTests(TestCase):
    def setUp(self):
        institution = Institution.objects.create(
            name="Kisumu Water Office",
            description="Water services",
            location="Kisumu",
        )
        Project.objects.create(
            name="Community Water Access Project",
            description="Boreholes and water kiosks",
            location="Kisumu",
            county="Kisumu",
            institution=institution,
            allocated_amount=Decimal("35000000"),
        )
        Project.objects.create(
            name="Kisumu Market Upgrade",
            description="Civic market works with no water mention in the title",
            location="Kisumu",
            county="Kisumu",
            institution=institution,
            allocated_amount=Decimal("12000000"),
        )
        roads = Institution.objects.create(name="Roads Department", location="Nairobi")
        Project.objects.create(
            name="Outer Ring Road",
            description="Includes a water drainage clause only in the description",
            location="Nairobi",
            county="Nairobi",
            institution=roads,
            allocated_amount=Decimal("80000000"),
        )
        Policy.objects.create(
            title="Water services policy",
            description="Demo policy on water",
            institution=institution,
        )
        document = SourceDocument.objects.create(
            title="Water budget annex",
            publisher="County Treasury",
        )
        Project.objects.get(name="Community Water Access Project").source_documents.add(document)
        bujumbura = Institution.objects.create(
            name="[DEMO] Bujumbura Water Service Desk",
            location="Bujumbura, Burundi",
        )
        Project.objects.create(
            name="[DEMO] Mukaza Public Standpipe Rehabilitation",
            description="Boreholes and water kiosks in Bujumbura",
            location="Mukaza",
            county="Bujumbura",
            country="BI",
            institution=bujumbura,
        )
        Policy.objects.create(
            title="[DEMO] Bujumbura water access policy",
            institution=bujumbura,
        )
        dar = Institution.objects.create(
            name="[DEMO] Dar es Salaam Water and Sanitation Desk",
            location="Dar es Salaam, Tanzania",
        )
        Project.objects.create(
            name="[DEMO] Dar es Salaam Water Network Repair",
            description="Piped water repairs",
            location="Dar es Salaam",
            county="Dar es Salaam",
            country="TZ",
            institution=dar,
        )

    def test_search_finds_projects_institutions_policies_and_documents(self):
        results = search_civic_data("water")
        self.assertGreaterEqual(results["total"], 4)
        self.assertTrue(any("Community Water" in p.name for p in results["projects"]))
        self.assertTrue(any("Kisumu Water" in i.name for i in results["institutions"]))
        self.assertTrue(any("Water services" in p.title for p in results["policies"]))
        self.assertTrue(any("Water budget" in d.title for d in results["documents"]))

    def test_empty_query_returns_nothing(self):
        results = search_civic_data("")
        self.assertEqual(results["total"], 0)

    def test_search_page_and_htmx_partial(self):
        response = self.client.get(reverse("core:search"), {"q": "water"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Community Water Access Project")

        htmx = self.client.get(
            reverse("core:search"),
            {"q": "water"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(htmx.status_code, 200)
        self.assertContains(htmx, "Community Water Access Project")
        self.assertNotContains(htmx, "<html")

    def test_live_suggest_ranks_name_matches_first(self):
        results = search_civic_data("water", suggest=True)
        names = [p.name for p in results["projects"]]
        self.assertGreaterEqual(results["project_count"], 1)
        self.assertEqual(names[0], "Community Water Access Project")
        self.assertNotIn("Outer Ring Road", names)

    def test_full_search_includes_description_matches(self):
        results = search_civic_data("water", suggest=False)
        names = [p.name for p in results["projects"]]
        self.assertIn("Outer Ring Road", names)
        self.assertIn("Kisumu Market Upgrade", names)

    def test_counts_are_not_the_returned_slice(self):
        extra = Institution.objects.get(name="Kisumu Water Office")
        for index in range(12):
            Project.objects.create(
                name=f"Water kiosk {index}",
                description="Neighbourhood water point",
                location="Kisumu",
                county="Kisumu",
                institution=extra,
            )
        results = search_civic_data("water", limit=3, suggest=True)
        self.assertEqual(len(results["projects"]), 3)
        self.assertGreater(results["project_count"], 3)
        self.assertEqual(
            results["total"],
            results["project_count"]
            + results["institution_count"]
            + results["policy_count"]
            + results["document_count"],
        )

    def test_short_live_query_is_ignored(self):
        results = search_civic_data("w", suggest=True)
        self.assertTrue(results["too_short"])
        self.assertEqual(results["total"], 0)

    def test_suggest_endpoint_returns_partial(self):
        response = self.client.get(reverse("core:search-suggest"), {"q": "water"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Community Water Access Project")
        self.assertContains(response, "View full results")
        self.assertNotContains(response, "<html")

        short = self.client.get(reverse("core:search-suggest"), {"q": "w"})
        self.assertContains(short, "Type at least 2 characters")

    def test_projects_kind_renders_editorial_hits(self):
        response = self.client.get(reverse("core:search"), {"kind": "projects"})
        self.assertContains(response, "search-project")
        self.assertContains(response, "Community Water Access Project")
        self.assertContains(response, "KSh")
        self.assertContains(response, "Evidence")

    def test_filters_narrow_projects(self):
        none = search_civic_data("water", county="Mombasa")
        self.assertEqual(none["project_count"], 0)
        nairobi = search_civic_data("water", county="Nairobi", kind="projects")
        self.assertEqual(nairobi["project_count"], 1)
        self.assertEqual(nairobi["institution_count"], 0)
        kisumu = search_civic_data("water", county="Kisumu", kind="projects")
        self.assertGreaterEqual(kisumu["project_count"], 1)
        self.assertEqual(kisumu["institution_count"], 0)

    def test_search_follows_request_country(self):
        kenya = search_civic_data("water")
        kenya_institutions = [item.name for item in kenya["institutions"]]
        kenya_projects = [item.name for item in kenya["projects"]]
        kenya_policies = [item.title for item in kenya["policies"]]
        self.assertTrue(any("Kisumu Water" in name for name in kenya_institutions))
        self.assertTrue(any("Community Water" in name for name in kenya_projects))
        self.assertTrue(any("Water services policy" in title for title in kenya_policies))
        self.assertFalse(any("Bujumbura" in name for name in kenya_institutions))
        self.assertFalse(any("Dar es Salaam" in name for name in kenya_institutions))
        self.assertFalse(any("Mukaza" in name for name in kenya_projects))
        self.assertFalse(any("Bujumbura" in title for title in kenya_policies))

        burundi = search_civic_data("water", country="BI")
        burundi_institutions = [item.name for item in burundi["institutions"]]
        burundi_projects = [item.name for item in burundi["projects"]]
        self.assertTrue(any("Bujumbura Water" in name for name in burundi_institutions))
        self.assertTrue(any("Mukaza" in name for name in burundi_projects))
        self.assertFalse(any("Kisumu Water" in name for name in burundi_institutions))
        self.assertFalse(any("Community Water Access" in name for name in burundi_projects))
        self.assertFalse(any("Dar es Salaam" in name for name in burundi_institutions))

        guest = self.client.get(reverse("core:search-suggest"), {"q": "water"})
        self.assertContains(guest, "Kisumu Water Office")
        self.assertNotContains(guest, "Bujumbura Water Service Desk")
        self.assertNotContains(guest, "Dar es Salaam Water and Sanitation Desk")
        self.assertNotContains(guest, "Bujumbura water access policy")

        from django.contrib.auth import get_user_model

        User = get_user_model()
        User.objects.create_user(username="bujumbura", password="pass12345", country="BI")
        self.client.login(username="bujumbura", password="pass12345")
        logged_in = self.client.get(reverse("core:search-suggest"), {"q": "water"})
        self.assertContains(logged_in, "Bujumbura Water Service Desk")
        self.assertNotContains(logged_in, "Kisumu Water Office")
        self.assertNotContains(logged_in, "Dar es Salaam Water and Sanitation Desk")
