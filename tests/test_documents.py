import tempfile

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.services.search import search_civic_data
from apps.sources.extraction import make_simple_docx, make_simple_pdf
from apps.sources.models import ExtractionStatus, SourceDocument


class DocumentPreviewAndSearchTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media.cleanup)
        self.pdf = SourceDocument.objects.create(
            title="County water budget annex",
            publisher="County Treasury",
            original_filename="water-budget.pdf",
        )
        self.pdf.file.save(
            "water-budget.pdf",
            ContentFile(make_simple_pdf("Allocation for community water access boreholes")),
            save=True,
        )
        self.docx = SourceDocument.objects.create(
            title="Water works tender pack",
            publisher="Procurement",
            original_filename="water-tender.docx",
        )
        self.docx.file.save(
            "water-tender.docx",
            ContentFile(make_simple_docx(["Tender notice", "Drill twelve boreholes in Kisumu"])),
            save=True,
        )
        self.pdf.refresh_from_db()
        self.docx.refresh_from_db()

    def test_extracted_text_is_searchable(self):
        self.assertEqual(self.pdf.extraction_status, ExtractionStatus.READY)
        self.assertIn("boreholes", self.pdf.extracted_text.lower())
        results = search_civic_data("boreholes")
        titles = [item.title for item in results["documents"]]
        self.assertIn(self.pdf.title, titles)
        self.assertIn(self.docx.title, titles)

    def test_filename_search(self):
        results = search_civic_data("water-tender.docx")
        self.assertTrue(any(item.pk == self.docx.pk for item in results["documents"]))

    def test_live_suggest_skips_body_text(self):
        results = search_civic_data("boreholes", suggest=True)
        self.assertFalse(any(item.pk == self.pdf.pk for item in results["documents"]))

    def test_documents_list_paginates(self):
        for index in range(13):
            SourceDocument.objects.create(
                title=f"Extra annex {index}",
                publisher="Demo",
            )
        response = self.client.get(reverse("sources:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Showing 1–12 of")
        self.assertContains(response, "Page 1 of")

    def test_pdf_preview_and_range_request(self):
        response = self.client.get(reverse("sources:file", args=[self.pdf.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertEqual(response.get("X-Frame-Options"), "SAMEORIGIN")

        ranged = self.client.get(
            reverse("sources:file", args=[self.pdf.pk]),
            HTTP_RANGE="bytes=0-10",
        )
        self.assertEqual(ranged.status_code, 206)
        self.assertEqual(ranged["Content-Length"], "11")
        self.assertTrue(ranged["Content-Range"].startswith("bytes 0-10/"))

    def test_docx_preview_renders_paragraphs(self):
        response = self.client.get(self.docx.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Drill twelve boreholes in Kisumu")
        self.assertContains(response, "Preview")
