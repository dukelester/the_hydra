from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.core.uploads import validate_upload
from apps.sources.extraction import extract_text, make_simple_docx, make_simple_pdf, make_simple_xlsx


class FileValidationTests(TestCase):
    def test_rejects_disallowed_extension(self):
        uploaded = SimpleUploadedFile("notes.exe", b"MZ", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_upload(uploaded)

    @override_settings(THEHYDRA_MAX_UPLOAD_BYTES=10 * 1024 * 1024)
    def test_rejects_oversize_file(self):
        uploaded = SimpleUploadedFile(
            "big.pdf",
            b"a" * (11 * 1024 * 1024),
            content_type="application/pdf",
        )
        with self.assertRaises(ValidationError):
            validate_upload(uploaded)

    def test_accepts_office_and_pdf_types(self):
        validate_upload(SimpleUploadedFile("note.pdf", b"%PDF", content_type="application/pdf"))
        validate_upload(
            SimpleUploadedFile(
                "note.docx",
                b"PK",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        )
        validate_upload(
            SimpleUploadedFile(
                "sheet.xlsx",
                b"PK",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        )

    def test_accepts_valid_png(self):
        buffer = BytesIO()
        Image.new("RGB", (2, 2), color="blue").save(buffer, format="PNG")
        uploaded = SimpleUploadedFile("photo.png", buffer.getvalue(), content_type="image/png")
        validate_upload(uploaded)

    def test_rejects_fake_image(self):
        uploaded = SimpleUploadedFile("photo.png", b"not-an-image", content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_upload(uploaded)


class TextExtractionTests(TestCase):
    def test_extracts_pdf_docx_and_xlsx(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as folder:
            pdf_path = Path(folder) / "a.pdf"
            pdf_path.write_bytes(make_simple_pdf("Community water access boreholes"))
            self.assertIn("water", extract_text(pdf_path, "a.pdf").lower())

            docx_path = Path(folder) / "a.docx"
            docx_path.write_bytes(make_simple_docx(["Tender notice", "Pipeline repairs in Kisumu"]))
            self.assertIn("pipeline", extract_text(docx_path, "a.docx").lower())

            xlsx_path = Path(folder) / "a.xlsx"
            xlsx_path.write_bytes(make_simple_xlsx([["Item", "Amount"], ["Solar lights", 1000]]))
            self.assertIn("solar", extract_text(xlsx_path, "a.xlsx").lower())
