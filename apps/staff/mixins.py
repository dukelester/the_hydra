from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class SearchQueryMixin:
    search_fields = ()

    def get_queryset(self):
        queryset = super().get_queryset()
        query = (self.request.GET.get("q") or "").strip()
        if query and self.search_fields:
            lookup = Q()
            for field in self.search_fields:
                lookup |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(lookup)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_q"] = (self.request.GET.get("q") or "").strip()
        return context
