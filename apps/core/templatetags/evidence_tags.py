from django import template

from apps.sources.models import EvidenceVerificationStatus

register = template.Library()

STATUS_LABELS = {
    EvidenceVerificationStatus.VERIFIED: "Verified",
    EvidenceVerificationStatus.PARTIALLY_VERIFIED: "Partially verified",
    EvidenceVerificationStatus.CONFLICTING: "Conflicting information",
    EvidenceVerificationStatus.UNKNOWN: "Unknown",
}


@register.inclusion_tag("components/evidence_badge.html")
def evidence_badge(status):
    return {
        "status": status,
        "label": STATUS_LABELS.get(status, status),
    }


@register.filter
def coverage_tone(percent):
    try:
        value = int(percent)
    except (TypeError, ValueError):
        return "limited"
    if value >= 70:
        return "strong"
    if value >= 40:
        return "partial"
    return "limited"
