from rest_framework import permissions
from rest_framework.exceptions import MethodNotAllowed


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
            return (request.user.is_moderator
                    or request.user.is_admin
                    or obj.author == request.user)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and request.user.is_admin)


class IsAdminOrReadOnly(IsAdmin):
    def has_permission(self, request, view):
        return (super().has_permission(request, view)
                or request.method in permissions.SAFE_METHODS)
