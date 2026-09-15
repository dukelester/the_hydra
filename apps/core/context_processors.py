from django.utils import translation

from apps.core.governance import country_profile, request_country


def site(request):
    language = translation.get_language() or "en"
    gov = country_profile(request_country(request))
    return {
        "site_name": "H.Y.D.R.A.",
        "site_tagline": "Human-centered Yield, Data, Rights & Accountability",
        "hydra_lite": getattr(request, "hydra_lite", False),
        "hydra_rtl": language.startswith("ar"),
        "governance": gov,
    }
