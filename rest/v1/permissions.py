from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedOrWriteOnly(BasePermission):

    def has_permission(self, request, view):
        allowed = False
        if request.method == 'POST':
            allowed = True
        elif request.method in SAFE_METHODS:
            allowed = request.user and request.user.is_authenticated()
        return allowed
