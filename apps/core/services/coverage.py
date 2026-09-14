from apps.projects.models import TIMELINE_STAGE_ORDER, TimelineStage
from apps.sources.models import EvidenceVerificationStatus

SUPPORTED_STATUSES = {
    EvidenceVerificationStatus.VERIFIED,
    EvidenceVerificationStatus.PARTIALLY_VERIFIED,
}


def calculate_evidence_coverage(project):
    """
    Evidence Coverage describes how much recorded project information is
    supported by evidence. It is not a corruption, fraud, or trust score.
    """
    evidence_items = list(project.evidence_items.all())
    counts = {
        EvidenceVerificationStatus.VERIFIED: 0,
        EvidenceVerificationStatus.PARTIALLY_VERIFIED: 0,
        EvidenceVerificationStatus.CONFLICTING: 0,
        EvidenceVerificationStatus.UNKNOWN: 0,
    }
    for item in evidence_items:
        counts[item.verification_status] = counts.get(item.verification_status, 0) + 1

    total_claims = len(evidence_items)
    supported = (
        counts[EvidenceVerificationStatus.VERIFIED]
        + counts[EvidenceVerificationStatus.PARTIALLY_VERIFIED]
    )
    percent = round((supported / total_claims) * 100) if total_claims else 0

    missing = collect_missing_information(project, evidence_items)

    return {
        "percent": percent,
        "supported": supported,
        "total_claims": total_claims,
        "verified": counts[EvidenceVerificationStatus.VERIFIED],
        "partially_verified": counts[EvidenceVerificationStatus.PARTIALLY_VERIFIED],
        "conflicting": counts[EvidenceVerificationStatus.CONFLICTING],
        "unknown": counts[EvidenceVerificationStatus.UNKNOWN],
        "missing": missing,
        "level": coverage_level(percent, total_claims),
    }


def coverage_level(percent, total_claims):
    if total_claims == 0:
        return "none"
    if percent >= 70:
        return "strong"
    if percent >= 40:
        return "partial"
    return "limited"


def collect_missing_information(project, evidence_items=None):
    """List information points that lack supporting evidence. Never guess values."""
    if evidence_items is None:
        evidence_items = list(project.evidence_items.select_related("source_document"))

    missing = []
    if not project.allocated_amount:
        missing.append("Allocated amount is not recorded.")
    if not project.contractor:
        missing.append("Contractor / implementing firm is not recorded.")
    if not project.financial_year:
        missing.append("Financial year is not recorded.")
    if not project.start_date:
        missing.append("Start date is not recorded.")
    if not project.expected_completion_date:
        missing.append("Expected completion date is not recorded.")
    if project.status == "unknown":
        missing.append("Project status is recorded as unknown.")
    if not project.allocations.exists():
        missing.append("No budget allocation records are attached.")
    if not project.source_documents.exists():
        missing.append("No source documents are attached to this project.")

    events = {event.stage: event for event in project.timeline_events.all()}
    for stage in TIMELINE_STAGE_ORDER:
        event = events.get(stage)
        label = TimelineStage(stage).label
        if event is None:
            missing.append(f"{label} stage: evidence unavailable.")
        elif not event.evidence_id:
            missing.append(f"{label} stage has a record, but no linked evidence.")

    for item in evidence_items:
        if item.verification_status == EvidenceVerificationStatus.UNKNOWN:
            missing.append(f'Claim lacks verified evidence: "{_clip(item.claim)}"')
        elif item.verification_status == EvidenceVerificationStatus.CONFLICTING:
            missing.append(f'Claim has conflicting evidence: "{_clip(item.claim)}"')
        elif not item.has_source():
            missing.append(f'Claim has no source document: "{_clip(item.claim)}"')

    # Preserve order while removing duplicates
    seen = set()
    unique = []
    for entry in missing:
        if entry not in seen:
            seen.add(entry)
            unique.append(entry)
    return unique


def _clip(text, length=90):
    text = (text or "").strip()
    if len(text) <= length:
        return text
    return text[: length - 1] + "…"
