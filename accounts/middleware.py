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
        if (request.path.startswith('/api/auth/') or 
            request.path.startswith('/api/token/') or
            request.path.startswith('/api/v1/auth/') or 
            request.path.startswith('/api/v1/token/')):
            return True
            
        # Skip for public endpoints
        if request.path.startswith('/api/public/') or request.path.startswith('/api/v1/public/'):
            return True
            
        # Skip for non-API paths
        if not (request.path.startswith('/api/') or request.path.startswith('/api/v1/')):
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
        Kiểm tra quyền truy cập đơn giản hóa
        """
        user = request.user
        path = request.path
        
        # Admin can access everything
        if hasattr(user, 'is_admin') and user.is_admin:
            return True
            
        # Check for admin URLs - non-admin users cannot access admin routes
        if ('admin' in path) and not (hasattr(user, 'is_admin') and user.is_admin):
            return False
            
        # For all other endpoints, let DRF permission classes handle it
        return True 