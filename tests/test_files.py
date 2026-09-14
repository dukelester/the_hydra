from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from apps.core.uploads import validate_upload


class FileValidationTests(TestCase):
    def test_rejects_disallowed_extension(self):
        uploaded = SimpleUploadedFile("notes.exe", b"MZ", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_upload(uploaded)

    def test_rejects_oversize_file(self):
        uploaded = SimpleUploadedFile(
            "big.pdf",
            b"a" * (11 * 1024 * 1024),
            content_type="application/pdf",
        )
        with self.assertRaises(ValidationError):
            validate_upload(uploaded)

    def test_accepts_valid_png(self):
        buffer = BytesIO()
        Image.new("RGB", (2, 2), color="blue").save(buffer, format="PNG")
        uploaded = SimpleUploadedFile("photo.png", buffer.getvalue(), content_type="image/png")
        validate_upload(uploaded)

    def test_rejects_fake_image(self):
        uploaded = SimpleUploadedFile("photo.png", b"not-an-image", content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_upload(uploaded)
