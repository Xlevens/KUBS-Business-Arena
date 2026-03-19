from rest_framework.permissions import BasePermission


class IsRoundHead(BasePermission):
    """Allow access only to authenticated round heads or superusers."""

    message = "You must be a round head or superuser to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.managed_rounds.exists()
