from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff and request.user.is_superuser)

class IsStaffUser(permissions.BasePermission):
    """
    Custom permission to allow staff users to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

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
        return obj == request.user or request.user.is_staff

class IsUserManager(permissions.BasePermission):
    """
    Quyền quản lý người dùng - dành cho staff có quyền quản lý user
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff and hasattr(request.user, 'can_manage_users') and request.user.can_manage_users)

class IsContentManager(permissions.BasePermission):
    """
    Quyền quản lý nội dung - dành cho staff có quyền quản lý nội dung
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff and hasattr(request.user, 'can_manage_content') and request.user.can_manage_content)

class IsPlaylistManager(permissions.BasePermission):
    """
    Quyền quản lý playlist - dành cho staff có quyền quản lý playlist
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff and hasattr(request.user, 'can_manage_playlists') and request.user.can_manage_playlists)

class IsPlaylistOwnerOrReadOnly(permissions.BasePermission):
    """
    Quyền quản lý playlist - chỉ chủ sở hữu mới có quyền chỉnh sửa
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Kiểm tra chủ sở hữu hoặc staff có quyền quản lý playlist
        is_owner = hasattr(obj, 'owner') and obj.owner == request.user
        is_manager = request.user.is_staff and hasattr(request.user, 'can_manage_playlists') and request.user.can_manage_playlists
        
        return is_owner or is_manager

class ReadOnly(permissions.BasePermission):
    """
    Chỉ cho phép đọc (GET, HEAD, OPTIONS)
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS 