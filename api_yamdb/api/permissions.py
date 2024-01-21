from rest_framework import permissions
from rest_framework.exceptions import MethodNotAllowed


class IsAuthorNotUserOrReadOnlyPermission(permissions.
                                          IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and obj.author == request.user)
            or (request.user.is_authenticated and request.user.role != 'user')
        )


class IsAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and request.user.role == 'admin')
        )


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == 'admin'


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


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'PUT':
            raise MethodNotAllowed('PUT')
        if request.method == 'GET':
            return True
        if request.method in ['PATCH', 'DELETE', 'POST']:
            return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True
        if request.method in ['PATCH', 'DELETE']:
            return request.user.role != 'user' or obj.author == request.user
