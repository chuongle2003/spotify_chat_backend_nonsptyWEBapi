from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Cho phép chỉ admin mới có quyền truy cập
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   hasattr(request.user, 'is_admin') and request.user.is_admin)

class IsMessageParticipant(permissions.BasePermission):
    """
    Cho phép quyền truy cập nếu người dùng là người gửi hoặc người nhận tin nhắn
    """
    def has_object_permission(self, request, view, obj):
        # Admin luôn có quyền truy cập
        if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return True
        # Người tham gia cuộc trò chuyện có quyền truy cập
        return obj.sender == request.user or obj.receiver == request.user

class IsReporter(permissions.BasePermission):
    """
    Cho phép quyền truy cập nếu người dùng là người báo cáo tin nhắn
    """
    def has_object_permission(self, request, view, obj):
        # Admin luôn có quyền truy cập
        if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return True
        # Người báo cáo có quyền truy cập
        return obj.reporter == request.user

class IsNotRestricted(permissions.BasePermission):
    """
    Chặn người dùng bị hạn chế không cho gửi tin nhắn
    """
    def has_permission(self, request, view):
        user = request.user
        
        # Admin luôn có quyền truy cập
        if hasattr(user, 'is_admin') and user.is_admin:
            return True
            
        # Kiểm tra nếu là POST request (gửi tin nhắn mới)
        if request.method == 'POST':
            from .models import ChatRestriction
            
            # Kiểm tra xem người dùng có bị hạn chế không
            active_restrictions = ChatRestriction.objects.filter(
                user=user,
                is_active=True
            )
            
            for restriction in active_restrictions:
                if not restriction.is_expired:
                    return False
                    
        return True 