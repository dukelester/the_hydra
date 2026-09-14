from django.db.models import Q
from django.views.generic import DetailView, ListView

from apps.policies.models import Policy


class PolicyListView(ListView):
    model = Policy
    template_name = "policies/list.html"
    context_object_name = "policies"
    paginate_by = 9

    def get_queryset(self):
        qs = Policy.objects.select_related("institution", "source_document")
        query = (self.request.GET.get("q") or "").strip()
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(institution__name__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class PolicyDetailView(DetailView):
    model = Policy
    template_name = "policies/detail.html"
    context_object_name = "policy"
    slug_field = "slug"

    def get_queryset(self):
        return Policy.objects.select_related("institution", "source_document")
