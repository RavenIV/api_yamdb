from rest_framework import permissions


class IsAuthorNotUserOrReadOnlyPermission(
        permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.role != 'user'
        )


class IsAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.role == 'admin' and request.user.is_authenticated
        )


class IsAdminOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.role == 'admin'
            or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user.role == 'admin'
            or request.user.is_superuser
        )
