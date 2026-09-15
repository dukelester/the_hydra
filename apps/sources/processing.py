"""Extract searchable text after the file is stored, without blocking the upload."""

from __future__ import annotations

import logging
import threading

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


def should_extract_async():
    if getattr(settings, "RUNNING_TESTS", False):
        return False
    return bool(getattr(settings, "THEHYDRA_EXTRACT_ASYNC", True))


def extract_document_now(document_pk):
    from apps.sources.extraction import extract_text
    from apps.sources.models import SourceDocument

    document = SourceDocument.objects.filter(pk=document_pk).first()
    if not document or not document.file:
        return
    text = extract_text(document.file.path, document.original_filename or document.file.name)
    document._store_extracted_text(text)


def schedule_document_extraction(document_pk):
    if should_extract_async():

        def start():
            worker = threading.Thread(
                target=_safe_extract,
                args=(document_pk,),
                daemon=True,
                name=f"hydra-extract-{document_pk}",
            )
            worker.start()

        transaction.on_commit(start)
        return
    extract_document_now(document_pk)


def _safe_extract(document_pk):
    try:
        extract_document_now(document_pk)
    except Exception:
        logger.exception("Could not extract text from document %s", document_pk)
