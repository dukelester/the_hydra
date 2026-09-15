"""Local next steps for a project file.

Steps stay practical and neutral: they do not accuse, and they are not
legal advice. The statute and oversight office follow the project's
country, or Kenya when the file has no country yet.
"""

from django.utils.translation import gettext as _

from apps.core.governance import DEFAULT_COUNTRY, country_profile, normalize_country


def project_next_steps(project, country=None):
    code = normalize_country(
        country
        or getattr(project, "country", None)
        or DEFAULT_COUNTRY
    )
    gov = country_profile(code)
    labels = gov["labels"]
    place = (project.county or "").strip() or _("your %(unit)s") % {"unit": labels["level1"].lower()}
    institution = project.institution.name if getattr(project, "institution", None) else _("the responsible office")
    missing = bool(getattr(project, "coverage", None) and project.coverage.get("missing"))
    law = gov["law"]

    steps = [
        {
            "kicker": _("1 · The file"),
            "title": _("Read what is missing"),
            "body": (
                _("This page lists claims, sources, and gaps. If a stage says evidence is unavailable, that is the starting point — not a finding of wrongdoing.")
                if missing
                else _("Read the timeline, budget, and source documents. Note what the file actually supports before you act.")
            ),
        },
        {
            "kicker": _("2 · The office"),
            "title": _("Ask %(institution)s") % {"institution": institution},
            "body": _(
                "Write to the implementing office and ask for the missing pages: budget vote, tender, contract, or completion certificate. Name the project and the financial year. Keep a copy of what you send."
            ),
        },
        {
            "kicker": _("3 · The law"),
            "title": _(law["title"]),
            "body": _(law["body"]),
            "extra": _("%(unit)s: %(place)s") % {"unit": labels["level1"], "place": place},
        },
        {
            "kicker": _("4 · What you saw"),
            "title": _("Record a citizen observation"),
            "body": _(
                "If you visited the site, write what you saw, when, and where. You can submit without an account. Do not include other people’s private details. An observation is not a finding."
            ),
        },
        {
            "kicker": _("5 · A structured file"),
            "title": _("Generate a private report"),
            "body": _(
                "A report puts official information and your observation in separate columns. Keep it private until you choose to share it with an oversight office, a journalist, or the %(assembly)s. It does not determine guilt."
            )
            % {"assembly": labels["assembly"]},
        },
    ]
    return steps, gov["name"]
