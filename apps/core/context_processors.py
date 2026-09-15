from django.utils import translation

from apps.core.access import wants_lite


def site(request):
    language = translation.get_language() or "en"
    return {
        "site_name": "H.Y.D.R.A.",
        "site_tagline": "Human-centered Yield, Data, Rights & Accountability",
        "hydra_lite": getattr(request, "hydra_lite", False),
        "hydra_rtl": language.startswith("ar"),
    }
