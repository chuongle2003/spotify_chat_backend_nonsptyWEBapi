from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   hasattr(request.user, 'is_admin') and request.user.is_admin)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object
        return obj == request.user or (hasattr(request.user, 'is_admin') and request.user.is_admin)

class ReadOnly(permissions.BasePermission):
    """
    Chỉ cho phép đọc (GET, HEAD, OPTIONS)
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS 