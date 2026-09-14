"""Extract searchable text from civic source files without loading whole files into RAM."""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from xml.etree.ElementTree import iterparse

from django.conf import settings

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def max_extract_chars():
    return int(getattr(settings, "THEHYDRA_MAX_EXTRACT_CHARS", 200_000))


def max_preview_rows():
    return int(getattr(settings, "THEHYDRA_PREVIEW_ROWS", 40))


def extension_of(name):
    return Path(name or "").suffix.lower()


def extract_text(path, filename=""):
    """
    Return extracted plain text, capped so large PDFs/spreadsheets stay searchable.
    Never raises — callers store an empty string on failure.
    """
    path = Path(path)
    ext = extension_of(filename) or path.suffix.lower()
    try:
        if ext == ".pdf":
            return _extract_pdf(path)
        if ext == ".docx":
            return _extract_docx(path)
        if ext == ".xlsx":
            return _extract_xlsx(path)
        if ext == ".csv":
            return _extract_csv(path)
        if ext in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")[: max_extract_chars()]
    except Exception:
        return ""
    return ""


def docx_preview_paragraphs(path, limit=None):
    limit = limit or max_preview_rows()
    paragraphs = []
    for text in _iter_docx_paragraphs(path):
        if text:
            paragraphs.append(text)
        if len(paragraphs) >= limit:
            break
    return paragraphs


def spreadsheet_preview(path, filename=""):
    ext = extension_of(filename) or Path(path).suffix.lower()
    if ext == ".csv":
        return [{"name": Path(filename or path).name or "Sheet", "rows": _csv_rows(path)}]
    if ext == ".xlsx":
        return _xlsx_preview(path)
    return []


def make_simple_pdf(text):
    """Tiny one-page PDF for tests and demo attachments."""
    safe = (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )
    stream = f"BT /F1 14 Tf 48 720 Td ({safe}) Tj ET\n"
    stream_bytes = stream.encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%b\nendstream" % (len(stream_bytes), stream_bytes),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in chunks))
        chunks.append(b"%d 0 obj\n%b\nendobj\n" % (index, body))
    xref_at = sum(len(part) for part in chunks)
    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = (
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        + str(xref_at).encode("ascii")
        + b"\n%%EOF\n"
    )
    return b"".join(chunks + xref + [trailer])


def _extract_pdf(path):
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    total = 0
    cap = max_extract_chars()
    for page in reader.pages:
        text = page.extract_text() or ""
        if not text:
            continue
        parts.append(text)
        total += len(text)
        if total >= cap:
            break
    return "\n".join(parts)[:cap]


def _iter_docx_paragraphs(path):
    with zipfile.ZipFile(path) as archive:
        with archive.open("word/document.xml") as handle:
            paragraph = []
            for event, elem in iterparse(handle, events=("end",)):
                tag = elem.tag
                if tag == f"{W_NS}t" and elem.text:
                    paragraph.append(elem.text)
                elif tag == f"{W_NS}p":
                    yield " ".join(paragraph).strip()
                    paragraph = []
                    elem.clear()
                else:
                    elem.clear()


def _extract_docx(path):
    cap = max_extract_chars()
    parts = []
    total = 0
    for text in _iter_docx_paragraphs(path):
        if not text:
            continue
        parts.append(text)
        total += len(text) + 1
        if total >= cap:
            break
    return "\n".join(parts)[:cap]


def _extract_xlsx(path):
    from openpyxl import load_workbook

    cap = max_extract_chars()
    workbook = load_workbook(filename=str(path), read_only=True, data_only=True)
    parts = []
    total = 0
    try:
        for sheet in workbook.worksheets:
            parts.append(sheet.title)
            for row in sheet.iter_rows(values_only=True):
                cells = [str(cell) for cell in row if cell is not None and str(cell).strip()]
                if not cells:
                    continue
                line = " ".join(cells)
                parts.append(line)
                total += len(line) + 1
                if total >= cap:
                    return "\n".join(parts)[:cap]
    finally:
        workbook.close()
    return "\n".join(parts)[:cap]


def _extract_csv(path):
    cap = max_extract_chars()
    parts = []
    total = 0
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            line = " ".join(cell.strip() for cell in row if cell and cell.strip())
            if not line:
                continue
            parts.append(line)
            total += len(line) + 1
            if total >= cap:
                break
    return "\n".join(parts)[:cap]


def _csv_rows(path):
    rows = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.reader(handle)
        for index, row in enumerate(reader):
            if index >= max_preview_rows():
                break
            rows.append(row)
    return rows


def _xlsx_preview(path):
    from openpyxl import load_workbook

    workbook = load_workbook(filename=str(path), read_only=True, data_only=True)
    sheets = []
    try:
        for sheet in workbook.worksheets[:3]:
            rows = []
            for index, row in enumerate(sheet.iter_rows(values_only=True)):
                if index >= max_preview_rows():
                    break
                rows.append(["" if cell is None else str(cell) for cell in row])
            sheets.append({"name": sheet.title, "rows": rows})
    finally:
        workbook.close()
    return sheets


def make_simple_docx(paragraphs):
    from docx import Document

    document = Document()
    for item in paragraphs:
        document.add_paragraph(item)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def make_simple_xlsx(rows, sheet_name="Budget"):
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
