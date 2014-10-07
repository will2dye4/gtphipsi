from rest_framework.permissions import BasePermission

from gtphipsi.common import get_rush_or_404


class IsAuthenticatedOrCurrentRush(BasePermission):

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated():
            allowed = True
        else:
            rush = get_rush_or_404(request.parser_context['kwargs']['name'])
            allowed = rush.is_current()
        return allowed
