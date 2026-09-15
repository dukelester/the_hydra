from django.utils import translation

from apps.core.governance import country_profile, user_country


def site(request):
    language = translation.get_language() or "en"
    user = getattr(request, "user", None)
    authenticated = bool(user and getattr(user, "is_authenticated", False))
    gov = country_profile(user_country(user) if authenticated else None)
    return {
        "site_name": "H.Y.D.R.A.",
        "site_tagline": "Human-centered Yield, Data, Rights & Accountability",
        "hydra_lite": getattr(request, "hydra_lite", False),
        "hydra_rtl": language.startswith("ar"),
        "governance": gov,
    }
