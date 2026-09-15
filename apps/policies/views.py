from django.views.generic import DetailView, ListView

from apps.core.governance import request_country
from apps.core.services.search import policy_search_queryset
from apps.policies.models import Policy


class PolicyListView(ListView):
    model = Policy
    template_name = "policies/list.html"
    context_object_name = "policies"
    paginate_by = 9

    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        return policy_search_queryset(query, country=request_country(self.request)).select_related(
            "source_document"
        )

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
