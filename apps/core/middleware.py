from django.utils.deprecation import MiddlewareMixin
from django.utils import translation

from apps.core.access import wants_lite


class AccessPreferencesMiddleware(MiddlewareMixin):
    """Attach lite-mode and document language direction on every request."""

    def process_request(self, request):
        request.hydra_lite = wants_lite(request)
        language = translation.get_language() or "en"
        request.hydra_rtl = language.startswith("ar")
