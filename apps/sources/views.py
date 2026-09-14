import mimetypes
import os
import re
from pathlib import Path

from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import escape_uri_path
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import DetailView, ListView

from apps.core.services.search import document_search_queryset, normalize_query
from apps.sources.extraction import docx_preview_paragraphs, spreadsheet_preview
from apps.sources.models import DocumentType, SourceDocument

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")
CHUNK = 64 * 1024


class SourceDocumentListView(ListView):
    model = SourceDocument
    template_name = "sources/list.html"
    context_object_name = "documents"
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get("q", "")
        document_type = self.request.GET.get("type", "")
        qs = document_search_queryset(query)
        if document_type:
            qs = qs.filter(document_type=document_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = normalize_query(self.request.GET.get("q", ""))
        for document in context["documents"]:
            document.search_snippet = document.snippet_for(query) if query else ""
        context.update(
            {
                "query": query,
                "selected_type": self.request.GET.get("type", ""),
                "type_choices": DocumentType.choices,
            }
        )
        return context


class SourceDocumentDetailView(DetailView):
    model = SourceDocument
    template_name = "sources/detail.html"
    context_object_name = "document"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.object
        context["preview"] = build_preview(document)
        context["query"] = self.request.GET.get("q", "")
        context["snippet"] = document.snippet_for(context["query"])
        return context


def build_preview(document):
    kind = document.preview_kind()
    preview = {"kind": kind, "large": bool(document.file_size and document.file_size > 20 * 1024 * 1024)}
    if not document.file:
        preview["kind"] = "none"
        return preview
    path = document.file.path
    if not os.path.exists(path):
        preview["kind"] = "missing"
        return preview
    if kind == "docx":
        preview["paragraphs"] = docx_preview_paragraphs(path)
    elif kind == "spreadsheet":
        preview["sheets"] = spreadsheet_preview(path, document.original_filename)
    return preview


@xframe_options_sameorigin
def source_file(request, pk):
    document = get_object_or_404(SourceDocument, pk=pk)
    return _stream_document(request, document, inline=True)


def source_download(request, pk):
    document = get_object_or_404(SourceDocument, pk=pk)
    return _stream_document(request, document, inline=False)


def _stream_document(request, document, inline=True):
    if not document.file:
        raise Http404("No file is attached.")
    path = document.file.path
    if not os.path.exists(path):
        raise Http404("File is missing.")
    filename = document.original_filename or Path(document.file.name).name
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        content_type = "application/pdf"
    elif ext == ".docx":
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    disposition = "inline" if inline else "attachment"
    safe_name = escape_uri_path(filename)
    extra = {
        "Content-Disposition": f"{disposition}; filename=\"{filename}\"; filename*=UTF-8''{safe_name}",
        "X-Content-Type-Options": "nosniff",
        "Accept-Ranges": "bytes",
    }
    return ranged_file_response(request, path, content_type, extra)


def ranged_file_response(request, path, content_type, extra_headers):
    file_size = os.path.getsize(path)
    range_header = request.headers.get("Range") or request.META.get("HTTP_RANGE")
    start = 0
    end = file_size - 1
    status = 200
    if range_header:
        match = RANGE_RE.fullmatch(range_header.strip())
        if not match:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{file_size}"
            return response
        start_s, end_s = match.groups()
        if not start_s and end_s:
            suffix = int(end_s)
            start = max(0, file_size - suffix)
            end = file_size - 1
        else:
            if start_s:
                start = int(start_s)
            if end_s:
                end = int(end_s)
            elif start_s:
                end = file_size - 1
        if start >= file_size or start > end:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{file_size}"
            return response
        end = min(end, file_size - 1)
        status = 206

    length = end - start + 1 if file_size else 0
    handle = open(path, "rb")
    if status == 200:
        response = FileResponse(handle, content_type=content_type, status=status)
        response["Content-Length"] = str(file_size)
    else:
        response = StreamingHttpResponse(
            _read_range(handle, start, length),
            content_type=content_type,
            status=status,
        )
        response["Content-Length"] = str(length)
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    for key, value in extra_headers.items():
        response[key] = value
    return response


def _read_range(handle, start, length):
    handle.seek(start)
    remaining = length
    try:
        while remaining > 0:
            chunk = handle.read(min(CHUNK, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
    finally:
        handle.close()
