"""Country governance: labels, FOI next steps, and first-level units.

Signup and tracking cover African countries only. Kenya keeps the full
county → constituency → ward tree. Other countries ship first-level units;
deeper units appear when a project record names them.
"""

from functools import lru_cache
from pathlib import Path

DEFAULT_COUNTRY = "KE"

_UNITS_PATH = Path(__file__).resolve().parent.parent / "projects" / "data" / "country_units.json"

_DEFAULT_LAW = {
    "title": "Request information in writing",
    "body": (
        "Write to the public body that holds the file. Name the project, the financial year, "
        "and where to send the reply. If your country has an access-to-information law or an "
        "ombudsman, that office is the next step when there is no useful answer."
    ),
}

# Labels describe how people track public works, not a ranking of the country.
COUNTRIES = {
    "KE": {
        "name": "Kenya",
        "currency": "KES",
        "currency_prefix": "KSh",
        "labels": {
            "level1": "County",
            "level1_plural": "counties",
            "level2": "Constituency",
            "level2_plural": "constituencies",
            "level3": "Ward",
            "level3_plural": "wards",
            "track": "Track my county",
            "whole": "Whole county",
            "assembly": "county assembly",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Kenya, the Access to Information Act, 2016 lets you ask a public body for records. "
                "Say what you need, why it is a public project file, and where to send the reply. "
                "If there is no useful answer, the Commission on Administrative Justice "
                "(Office of the Ombudsman) is the national oversight office for access to information."
            ),
        },
    },
    "UG": {
        "name": "Uganda",
        "currency": "UGX",
        "currency_prefix": "USh",
        "labels": {
            "level1": "District",
            "level1_plural": "districts",
            "level2": "County",
            "level2_plural": "counties",
            "level3": "Sub-county",
            "level3_plural": "sub-counties",
            "track": "Track my district",
            "whole": "Whole district",
            "assembly": "district council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Uganda, the Access to Information Act, 2005 lets you ask a public body for records. "
                "Put the request in writing, name the project, and say where to send the reply. "
                "If there is no useful answer, the Uganda Human Rights Commission handles access-to-information complaints."
            ),
        },
    },
    "TZ": {
        "name": "Tanzania",
        "currency": "TZS",
        "currency_prefix": "TSh",
        "labels": {
            "level1": "Region",
            "level1_plural": "regions",
            "level2": "District",
            "level2_plural": "districts",
            "level3": "Ward",
            "level3_plural": "wards",
            "track": "Track my region",
            "whole": "Whole region",
            "assembly": "regional or district council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Tanzania, the Access to Information Act, 2016 lets you ask a public body for records. "
                "Name the project and the financial year, and say where to send the reply. "
                "If there is no useful answer, the Commission for Human Rights and Good Governance is the national oversight office."
            ),
        },
    },
    "BI": {
        "name": "Burundi",
        "currency": "BIF",
        "currency_prefix": "FBu",
        "labels": {
            "level1": "Province",
            "level1_plural": "provinces",
            "level2": "Commune",
            "level2_plural": "communes",
            "level3": "Zone",
            "level3_plural": "zones",
            "track": "Track my province",
            "whole": "Whole province",
            "assembly": "communal or provincial council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "Burundi does not yet have a standalone access-to-information statute. "
                "The Constitution recognizes the right to information. Write to the public body that holds the file. "
                "Name the project, the financial year, and where to send the reply. "
                "If there is no useful answer, the Ombudsman (Médiateur de la République) is a national civic route. "
                "This is not legal advice."
            ),
        },
    },
    "RW": {
        "name": "Rwanda",
        "currency": "RWF",
        "currency_prefix": "FRw",
        "labels": {
            "level1": "Province",
            "level1_plural": "provinces",
            "level2": "District",
            "level2_plural": "districts",
            "level3": "Sector",
            "level3_plural": "sectors",
            "track": "Track my province",
            "whole": "Whole province",
            "assembly": "district council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Rwanda, Law No. 04/2013 on access to information lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the Office of the Ombudsman oversees access to information."
            ),
        },
    },
    "ET": {
        "name": "Ethiopia",
        "currency": "ETB",
        "currency_prefix": "Br",
        "labels": {
            "level1": "Region",
            "level1_plural": "regions",
            "level2": "Zone",
            "level2_plural": "zones",
            "level3": "Woreda",
            "level3_plural": "woredas",
            "track": "Track my region",
            "whole": "Whole region",
            "assembly": "regional council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Ethiopia, Proclamation No. 590/2008 on the mass media and freedom of information lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, take the request to the institution that supervises that public body, or to the Ethiopian Human Rights Commission."
            ),
        },
    },
    "ZA": {
        "name": "South Africa",
        "currency": "ZAR",
        "currency_prefix": "R",
        "labels": {
            "level1": "Province",
            "level1_plural": "provinces",
            "level2": "Municipality",
            "level2_plural": "municipalities",
            "level3": "Ward",
            "level3_plural": "wards",
            "track": "Track my province",
            "whole": "Whole province",
            "assembly": "provincial legislature or municipal council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In South Africa, the Promotion of Access to Information Act, 2000 (PAIA) lets you ask a public body for records. "
                "Use the body’s PAIA form, name the project, and say where to send the reply. "
                "If there is no useful answer, the Information Regulator is the national oversight office."
            ),
        },
    },
    "NG": {
        "name": "Nigeria",
        "currency": "NGN",
        "currency_prefix": "₦",
        "labels": {
            "level1": "State",
            "level1_plural": "states",
            "level2": "Local Government Area",
            "level2_plural": "local government areas",
            "level3": "Ward",
            "level3_plural": "wards",
            "track": "Track my state",
            "whole": "Whole state",
            "assembly": "state house of assembly",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Nigeria, the Freedom of Information Act, 2011 lets you ask a public institution for records. "
                "Put the request in writing, name the project, and say where to send the reply. "
                "If there is no useful answer, you can apply to a court. The Public Complaints Commission is a further civic route."
            ),
        },
    },
    "GH": {
        "name": "Ghana",
        "currency": "GHS",
        "currency_prefix": "GH₵",
        "labels": {
            "level1": "Region",
            "level1_plural": "regions",
            "level2": "District",
            "level2_plural": "districts",
            "level3": "Electoral area",
            "level3_plural": "electoral areas",
            "track": "Track my region",
            "whole": "Whole region",
            "assembly": "district assembly",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Ghana, the Right to Information Act, 2019 (Act 989) lets you ask a public institution for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the Right to Information Commission is the national oversight office."
            ),
        },
    },
    "SN": {
        "name": "Senegal",
        "currency": "XOF",
        "currency_prefix": "CFA",
        "labels": {
            "level1": "Region",
            "level1_plural": "regions",
            "level2": "Department",
            "level2_plural": "departments",
            "level3": "Commune",
            "level3_plural": "communes",
            "track": "Track my region",
            "whole": "Whole region",
            "assembly": "conseil départemental or régional",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Senegal, Law No. 2018-25 on access to information lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the Commission d’accès à l’information is the national oversight office."
            ),
        },
    },
    "CI": {
        "name": "Côte d’Ivoire",
        "currency": "XOF",
        "currency_prefix": "CFA",
        "labels": {
            "level1": "District",
            "level1_plural": "districts",
            "level2": "Region",
            "level2_plural": "regions",
            "level3": "Department",
            "level3_plural": "departments",
            "track": "Track my district",
            "whole": "Whole district",
            "assembly": "conseil régional",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Côte d’Ivoire, Law No. 2013-867 on access to information of public interest lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the Commission d’accès à l’information d’intérêt public et aux documents publics (CAIDP) is the oversight office."
            ),
        },
    },
    "MZ": {
        "name": "Mozambique",
        "currency": "MZN",
        "currency_prefix": "MT",
        "labels": {
            "level1": "Province",
            "level1_plural": "provinces",
            "level2": "District",
            "level2_plural": "districts",
            "level3": "Administrative post",
            "level3_plural": "administrative posts",
            "track": "Track my province",
            "whole": "Whole province",
            "assembly": "assembleia provincial",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Mozambique, Law No. 34/2014 on the right to information lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, take the request to the entity that oversees that public body, or to the national human rights commission."
            ),
        },
    },
    "ML": {
        "name": "Mali",
        "currency": "XOF",
        "currency_prefix": "CFA",
        "labels": {
            "level1": "Region",
            "level1_plural": "regions",
            "level2": "Cercle",
            "level2_plural": "cercles",
            "level3": "Commune",
            "level3_plural": "communes",
            "track": "Track my region",
            "whole": "Whole region",
            "assembly": "conseil régional",
        },
        "law": _DEFAULT_LAW,
    },
    "BF": {
        "name": "Burkina Faso",
        "currency": "XOF",
        "currency_prefix": "CFA",
        "labels": {
            "level1": "Region",
            "level1_plural": "regions",
            "level2": "Province",
            "level2_plural": "provinces",
            "level3": "Department",
            "level3_plural": "departments",
            "track": "Track my region",
            "whole": "Whole region",
            "assembly": "conseil régional",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Burkina Faso, Law No. 051-2015 on access to public information lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the Autorité de régulation de la communication électronique et des postes has a role in access disputes, and the Médiateur du Faso is a further civic route."
            ),
        },
    },
    "CD": {
        "name": "Democratic Republic of the Congo",
        "currency": "CDF",
        "currency_prefix": "FC",
        "labels": {
            "level1": "Province",
            "level1_plural": "provinces",
            "level2": "Territory",
            "level2_plural": "territories",
            "level3": "Sector",
            "level3_plural": "sectors",
            "track": "Track my province",
            "whole": "Whole province",
            "assembly": "provincial assembly",
        },
        "law": _DEFAULT_LAW,
    },
    "AO": {
        "name": "Angola",
        "currency": "AOA",
        "currency_prefix": "Kz",
        "labels": {
            "level1": "Province",
            "level1_plural": "provinces",
            "level2": "Municipality",
            "level2_plural": "municipalities",
            "level3": "Commune",
            "level3_plural": "communes",
            "track": "Track my province",
            "whole": "Whole province",
            "assembly": "assembleia provincial",
        },
        "law": _DEFAULT_LAW,
    },
    "ZW": {
        "name": "Zimbabwe",
        "currency": "USD",
        "currency_prefix": "US$",
        "labels": {
            "level1": "Province",
            "level1_plural": "provinces",
            "level2": "District",
            "level2_plural": "districts",
            "level3": "Ward",
            "level3_plural": "wards",
            "track": "Track my province",
            "whole": "Whole province",
            "assembly": "provincial or rural district council",
        },
        "law": _DEFAULT_LAW,
    },
    "ZM": {
        "name": "Zambia",
        "currency": "ZMW",
        "currency_prefix": "K",
        "labels": {
            "level1": "Province",
            "level1_plural": "provinces",
            "level2": "District",
            "level2_plural": "districts",
            "level3": "Ward",
            "level3_plural": "wards",
            "track": "Track my province",
            "whole": "Whole province",
            "assembly": "council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Zambia, the Access to Information Act, 2023 lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the office designated under that Act is the next national step."
            ),
        },
    },
    "MW": {
        "name": "Malawi",
        "currency": "MWK",
        "currency_prefix": "MK",
        "labels": {
            "level1": "District",
            "level1_plural": "districts",
            "level2": "Traditional authority",
            "level2_plural": "traditional authorities",
            "level3": "Ward",
            "level3_plural": "wards",
            "track": "Track my district",
            "whole": "Whole district",
            "assembly": "district council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Malawi, the Access to Information Act, 2017 lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the Malawi Human Rights Commission oversees the Act."
            ),
        },
    },
    "EG": {
        "name": "Egypt",
        "currency": "EGP",
        "currency_prefix": "E£",
        "labels": {
            "level1": "Governorate",
            "level1_plural": "governorates",
            "level2": "Markaz",
            "level2_plural": "marakiz",
            "level3": "Village or district",
            "level3_plural": "villages or districts",
            "track": "Track my governorate",
            "whole": "Whole governorate",
            "assembly": "local council",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "Egypt does not yet have a dedicated access-to-information statute. "
                "Write to the implementing ministry or governorate that holds the file, name the project, and keep a copy. "
                "The Administrative Control Authority and the House of Representatives are further civic routes. This is not legal advice."
            ),
        },
    },
    "TN": {
        "name": "Tunisia",
        "currency": "TND",
        "currency_prefix": "DT",
        "labels": {
            "level1": "Governorate",
            "level1_plural": "governorates",
            "level2": "Delegation",
            "level2_plural": "delegations",
            "level3": "Sector",
            "level3_plural": "sectors",
            "track": "Track my governorate",
            "whole": "Whole governorate",
            "assembly": "conseil régional or municipal",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Tunisia, Organic Law 2016-22 on access to information lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the Instance d’accès à l’information (INAI) is the national oversight office."
            ),
        },
    },
    "MA": {
        "name": "Morocco",
        "currency": "MAD",
        "currency_prefix": "DH",
        "labels": {
            "level1": "Region",
            "level1_plural": "regions",
            "level2": "Province",
            "level2_plural": "provinces",
            "level3": "Commune",
            "level3_plural": "communes",
            "track": "Track my region",
            "whole": "Whole region",
            "assembly": "conseil régional",
        },
        "law": {
            "title": "Request information in writing",
            "body": (
                "In Morocco, Law 31-13 on the right of access to information lets you ask a public body for records. "
                "Name the project and where to send the reply. "
                "If there is no useful answer, the Commission nationale du droit d’accès à l’information (CNDAI) is the national oversight office."
            ),
        },
    },
}


def normalize_country(code):
    code = (code or "").strip().upper()
    if code in COUNTRIES:
        return code
    return DEFAULT_COUNTRY


def country_profile(code=None):
    profile = COUNTRIES[normalize_country(code)]
    return {
        "code": normalize_country(code),
        "name": profile["name"],
        "currency": profile["currency"],
        "currency_prefix": profile["currency_prefix"],
        "labels": profile["labels"],
        "law": profile.get("law") or _DEFAULT_LAW,
    }


def country_choices():
    items = [(code, data["name"]) for code, data in COUNTRIES.items()]
    items.sort(key=lambda item: (item[0] != DEFAULT_COUNTRY, item[1]))
    return items


def user_country(user):
    if user is None or not getattr(user, "is_authenticated", False):
        return DEFAULT_COUNTRY
    return normalize_country(getattr(user, "country", None))


def request_country(request):
    """Country for filters and lists. Guests and blank signups use Kenya."""
    user = getattr(request, "user", None)
    return user_country(user)


@lru_cache(maxsize=1)
def _country_units():
    import json

    if not _UNITS_PATH.exists():
        return {}
    return json.loads(_UNITS_PATH.read_text(encoding="utf-8"))


def country_unit_names(code):
    code = normalize_country(code)
    if code == DEFAULT_COUNTRY:
        return []
    return list(_country_units().get(code, []))
