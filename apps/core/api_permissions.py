from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticatedOrReadOnly

from apps.core.permissions import can_view_investigation, can_view_report


class IsOwnerOrStaffOrSession(BasePermission):
    """Private investigations and reports: owner, staff, or session token."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            model_name = obj.__class__.__name__
            if model_name == "Investigation":
                return can_view_investigation(request, obj)
            if model_name == "IssueReport":
                return can_view_report(request, obj)
        user = request.user
        if user and user.is_authenticated and (user.is_staff or getattr(obj, "user_id", None) == user.id):
            return True
        return False


class ReadOnlyOrCreateInvestigation(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.method == "POST"
