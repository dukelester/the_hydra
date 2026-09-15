SESSION_INVESTIGATIONS = "investigation_ids"
SESSION_REPORTS = "report_ids"


def _as_id(value):
    return str(value)


def remember_id(request, session_key, pk):
    key = _as_id(pk)
    ids = [_as_id(item) for item in request.session.get(session_key, [])]
    if key not in ids:
        ids.append(key)
    request.session[session_key] = ids
    request.session.modified = True


def session_has_id(request, session_key, pk):
    ids = {_as_id(item) for item in request.session.get(session_key, [])}
    return _as_id(pk) in ids


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
