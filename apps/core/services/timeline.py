from apps.projects.models import TIMELINE_STAGE_ORDER, TimelineStage


def build_project_timeline(project):
    """
    Return the six Follow-the-Money stages for a project.

    Missing stages are included with an explicit 'Evidence unavailable' flag.
    This function never invents facts.
    """
    events = {event.stage: event for event in project.timeline_events.all()}
    timeline = []
    for index, stage in enumerate(TIMELINE_STAGE_ORDER):
        event = events.get(stage)
        has_evidence = bool(event and event.evidence_id)
        timeline.append(
            {
                "stage": stage,
                "stage_label": TimelineStage(stage).label,
                "event": event,
                "has_event": event is not None,
                "has_evidence": has_evidence,
                "evidence_unavailable": not has_evidence,
                "position": index,
            }
        )
    return timeline
