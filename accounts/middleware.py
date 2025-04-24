from django.http import HttpResponseForbidden
from django.urls import resolve
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PermissionMiddleware:
    """
    Middleware kiểm tra quyền truy cập vào các endpoints
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for non-authenticated paths
        if self._should_skip_permission_check(request):
            return self.get_response(request)
            
        # Check permissions
        has_permission = self._check_permissions(request)
        if not has_permission:
            logger.warning(f"Permission denied for user {request.user} accessing {request.path}")
            return HttpResponseForbidden("You don't have permission to access this resource")
            
        return self.get_response(request)
        
    def _should_skip_permission_check(self, request):
        """
        Bỏ qua kiểm tra quyền cho các endpoint không cần xác thực
        """
        # Skip for authentication endpoints
        if request.path.startswith('/api/auth/') or request.path.startswith('/api/token/'):
            return True
            
        # Skip for public endpoints
        if request.path.startswith('/api/public/'):
            return True
            
        # Skip for non-API paths
        if not request.path.startswith('/api/'):
            return True
            
        # Skip for CORS preflight requests
        if request.method == 'OPTIONS':
            return True
            
        # Skip for non-authenticated users (they'll be handled by DRF permissions)
        if not request.user.is_authenticated:
            return True
            
        return False
        
    def _check_permissions(self, request):
        """
        Kiểm tra quyền truy cập
        """
        user = request.user
        path = request.path
        
        # Admin can access everything
        if user.is_superuser:
            return True
            
        # Check for admin URLs
        if 'admin' in path and not user.is_staff:
            return False
            
        # Check for user management endpoints
        if 'user-management' in path and not user.is_user_manager:
            return False
            
        # Check for content management endpoints
        if 'content' in path and not user.is_content_manager:
            return False
            
        # Check for playlist management endpoints
        if 'playlist-management' in path and not user.is_playlist_manager:
            return False
            
        # For all other endpoints, let DRF permission classes handle it
        return True 