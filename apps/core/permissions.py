SESSION_INVESTIGATIONS = "investigation_ids"
SESSION_REPORTS = "report_ids"


def remember_id(request, session_key, pk):
    ids = [int(x) for x in request.session.get(session_key, [])]
    if pk not in ids:
        ids.append(pk)
    request.session[session_key] = ids
    request.session.modified = True


def session_has_id(request, session_key, pk):
    ids = {int(x) for x in request.session.get(session_key, [])}
    return int(pk) in ids


def can_view_investigation(request, investigation):
    user = getattr(request, "user", None)
    if user and user.is_authenticated and (user.is_staff or investigation.user_id == user.id):
        return True
    return session_has_id(request, SESSION_INVESTIGATIONS, investigation.pk)


def can_view_report(request, report):
    if report.is_public:
        return True
    user = getattr(request, "user", None)
    if user and user.is_authenticated and (user.is_staff or report.user_id == user.id):
        return True
    return session_has_id(request, SESSION_REPORTS, report.pk)


def can_create_report_for_investigation(request, investigation):
    return can_view_investigation(request, investigation)
