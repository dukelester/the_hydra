from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.projects.models import Institution, Project
from apps.policies.models import Policy
from apps.sources.models import SourceDocument
from apps.core.services.search import search_civic_data


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
        Policy.objects.create(
            title="Water services policy",
            description="Demo policy on water",
            institution=institution,
        )
        SourceDocument.objects.create(
            title="Water budget annex",
            publisher="County Treasury",
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
