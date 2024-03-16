from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser or (
                request.method in SAFE_METHODS and request.user.is_authenticated))
