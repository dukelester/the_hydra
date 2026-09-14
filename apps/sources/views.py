from django.views.generic import DetailView

from apps.sources.models import SourceDocument


class SourceDocumentDetailView(DetailView):
    model = SourceDocument
    template_name = "sources/detail.html"
    context_object_name = "document"
