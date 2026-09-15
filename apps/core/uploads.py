import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.text import get_valid_filename
from PIL import Image, UnidentifiedImageError


@deconstructible
class SafeUploadTo:
    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        original = get_valid_filename(filename)
        ext = Path(original).suffix.lower()
        name = uuid.uuid4().hex
        return os.path.join("uploads", self.folder, f"{name}{ext}")

    def __eq__(self, other):
        return isinstance(other, SafeUploadTo) and self.folder == other.folder


def validate_upload(file):
    """Reject oversized or disallowed uploads. Large files are stored on disk, not in memory."""
    max_bytes = getattr(settings, "THEHYDRA_MAX_UPLOAD_BYTES", 200 * 1024 * 1024)
    allowed_ext = getattr(settings, "THEHYDRA_ALLOWED_UPLOAD_EXTENSIONS", default_allowed_extensions())
    allowed_types = getattr(
        settings,
        "THEHYDRA_ALLOWED_UPLOAD_CONTENT_TYPES",
        default_allowed_content_types(),
    )

    size = getattr(file, "size", 0) or 0
    if size > max_bytes:
        raise ValidationError(
            f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB."
        )

    name = getattr(file, "name", "") or ""
    ext = Path(name).suffix.lower()
    if ext not in allowed_ext:
        raise ValidationError(
            "This file type is not allowed. Upload a PDF, Word (.docx), Excel (.xlsx), CSV, or image."
        )

    content_type = (getattr(file, "content_type", "") or "").lower()
    if content_type and content_type not in allowed_types and content_type != "application/octet-stream":
        raise ValidationError("This file type is not allowed.")

    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        _validate_image(file)


def default_allowed_extensions():
    return {
        ".pdf",
        ".docx",
        ".xlsx",
        ".csv",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".txt",
    }


def default_allowed_content_types():
    return {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
        "text/plain",
        "image/jpeg",
        "image/png",
        "image/webp",
    }


def _validate_image(file):
    position = file.tell() if hasattr(file, "tell") else None
    try:
        image = Image.open(file)
        image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("The uploaded image could not be read.") from exc
    finally:
        if hasattr(file, "seek"):
            file.seek(position or 0)
