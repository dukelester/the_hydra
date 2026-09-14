from django.views.generic import DetailView, ListView

from apps.policies.models import Policy


class PolicyListView(ListView):
    model = Policy
    template_name = "policies/list.html"
    context_object_name = "policies"
    paginate_by = 20


class PolicyDetailView(DetailView):
    model = Policy
    template_name = "policies/detail.html"
    context_object_name = "policy"
    slug_field = "slug"

    def get_queryset(self):
        return Policy.objects.select_related("institution", "source_document")
