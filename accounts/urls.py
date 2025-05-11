from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, AdminViewSet,  # Thêm AdminViewSet vào import
    # Sửa lại các imports phù hợp với views.py
    UserSuggestionsView,
    ConnectionRequestView, AcceptConnectionView, 
    DeclineConnectionView, RemoveConnectionView,
    BlockUserView, PendingConnectionsView,
    ConnectedUsersView, CanChatWithUserView,
    UserListView, PublicUserListView,
    ForgotPasswordView, VerifyPasswordResetTokenView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView as LoginView,
    TokenRefreshView,
    TokenVerifyView
)

# Đăng ký các viewsets với router để tạo URLs tự động
router = DefaultRouter()
router.register(r'users', UserViewSet)

# Tạo router riêng cho admin APIs
admin_router = DefaultRouter()
admin_router.register(r'users', AdminViewSet)

urlpatterns = [
    # Include router URLs cho user thông thường
    path('', include(router.urls)),
    
    # Admin API endpoints - tách riêng khỏi Django admin
    path('admin/', include(admin_router.urls)),
    
    # Các endpoints xác thực JWT
    path('token/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API danh sách người dùng công khai
    path('public/users/', PublicUserListView.as_view(), name='public-users'),
    
    # API danh sách người dùng
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/suggestions/', UserSuggestionsView.as_view(), name='user_suggestions'),
    
    # API quản lý kết nối
    path('connections/request/<int:user_id>/', ConnectionRequestView.as_view(), name='connection_request'),
    path('connections/accept/<int:connection_id>/', AcceptConnectionView.as_view(), name='accept_connection'),
    path('connections/decline/<int:connection_id>/', DeclineConnectionView.as_view(), name='decline_connection'),
    path('connections/remove/<int:user_id>/', RemoveConnectionView.as_view(), name='remove_connection'),
    path('connections/block/<int:user_id>/', BlockUserView.as_view(), name='block_user'),
    
    # API danh sách kết nối
    path('connections/pending/', PendingConnectionsView.as_view(), name='pending_connections'),
    path('connections/users/', ConnectedUsersView.as_view(), name='connected_users'),
    
    # API kiểm tra quyền chat
    path('chat/can-chat/<str:username>/', CanChatWithUserView.as_view(), name='can_chat_with_user'),
    
    # API quên mật khẩu
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', VerifyPasswordResetTokenView.as_view(), name='reset_password'),
] 