from apps.reports.models import IssueReport, ReportStatus
from apps.sources.models import EvidenceVerificationStatus


DEFAULT_NEXT_STEPS = """1. Request the cited source documents from the responsible institution.
2. Compare official completion or budget claims with dated observations and attached evidence.
3. Seek written clarification from the implementing institution.
4. If the difference remains unresolved, submit this report to the relevant oversight office.
5. Do not treat this report as a finding of wrongdoing. It records a potential discrepancy that requires further verification."""


def generate_report_from_investigation(investigation, *, user=None, status=ReportStatus.DRAFT):
    """
    Build a structured accountability report from an investigation.

    Language stays neutral. No AI. No accusations.
    """
    project = investigation.project
    official = investigation.official_information.strip()
    observation = investigation.observation.strip()
    difference = investigation.difference_description.strip()

    evidence_summary = _build_evidence_summary(investigation)
    potential_discrepancy = (
        f"Official information states: “{official}” "
        f"A citizen observation recorded on {investigation.observed_at.isoformat()} "
        f"at {investigation.location} states: “{observation}” "
        f"Described difference: {difference} "
        "These accounts differ and require further verification. "
        "This report does not determine wrongdoing."
    )

    title = f"Accountability report: {project.name}"
    report = IssueReport.objects.create(
        project=project,
        investigation=investigation,
        user=user if user and getattr(user, "is_authenticated", False) else investigation.user,
        title=title,
        official_information=official,
        citizen_observation=observation,
        evidence_summary=evidence_summary,
        potential_discrepancy=potential_discrepancy,
        recommended_next_steps=DEFAULT_NEXT_STEPS,
        status=status,
        is_public=False,
    )
    return report


def _build_evidence_summary(investigation):
    project = investigation.project
    lines = []
    if investigation.evidence_description:
        lines.append(f"Citizen-submitted evidence description: {investigation.evidence_description}")
    file_count = investigation.file_count()
    if file_count:
        lines.append(
            f"{file_count} supporting file{'s' if file_count != 1 else ''} "
            "attached to the citizen observation."
        )
    else:
        lines.append("No supporting file was attached to the citizen observation.")

    items = list(project.evidence_items.select_related("source_document")[:12])
    if items:
        lines.append("Recorded project evidence:")
        for item in items:
            source = item.source_document.title if item.source_document else "Source unavailable"
            page = f", page {item.page_number}" if item.page_number else ""
            status = item.get_verification_status_display()
            lines.append(f'- Claim: "{item.claim}" Evidence: {item.evidence_text or "Evidence unavailable"} ({source}{page}; {status})')
    else:
        lines.append("No project evidence records are currently attached.")

    conflicting = project.evidence_items.filter(
        verification_status=EvidenceVerificationStatus.CONFLICTING
    ).count()
    if conflicting:
        lines.append(
            f"{conflicting} recorded claim(s) are marked as conflicting and require further verification."
        )
    return "\n".join(lines)
