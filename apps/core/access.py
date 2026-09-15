from django.utils.translation import gettext as _


def wants_lite(request):
    """True when the user asked for a lighter page or the browser sent Save-Data."""
    choice = request.session.get("hydra_lite")
    if choice is True:
        return True
    if choice is False:
        return False
    return request.headers.get("Save-Data", "").lower() == "on"


def set_lite(request, enabled):
    request.session["hydra_lite"] = bool(enabled)
    request.session.modified = True
