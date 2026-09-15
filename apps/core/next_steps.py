"""Local next steps for a project file.

Kenya is the first jurisdiction on this record. Steps stay practical and
neutral: they do not accuse, and they are not legal advice. Other
communities can replace the contacts and statutes without changing the
evidence model.
"""

from django.utils.translation import gettext as _


def project_next_steps(project):
    county = (project.county or "").strip() or _("your county")
    institution = project.institution.name if getattr(project, "institution", None) else _("the responsible office")
    missing = bool(getattr(project, "coverage", None) and project.coverage.get("missing"))

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
            "title": _("Request information in writing"),
            "body": _(
                "In Kenya, the Access to Information Act, 2016 lets you ask a public body for records. Say what you need, why it is a public project file, and where to send the reply. If there is no useful answer, the Commission on Administrative Justice (Office of the Ombudsman) is the national oversight office for access to information."
            ),
            "extra": _("County: %(county)s") % {"county": county},
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
                "A report puts official information and your observation in separate columns. Keep it private until you choose to share it with an oversight office, a journalist, or the county assembly. It does not determine guilt."
            ),
        },
    ]
    return steps
