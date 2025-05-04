from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, 
    # Sửa lại các imports phù hợp với views.py
    UserSuggestionsView,
    ConnectionRequestView, AcceptConnectionView, 
    DeclineConnectionView, RemoveConnectionView,
    BlockUserView, PendingConnectionsView,
    ConnectedUsersView, CanChatWithUserView,
    UserListView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView as LoginView,
    TokenRefreshView,
    TokenVerifyView
)

# Đăng ký các viewsets với router để tạo URLs tự động
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Các endpoints xác thực JWT
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API danh sách người dùng
    path('api/users/', UserListView.as_view(), name='user_list'),
    path('api/users/suggestions/', UserSuggestionsView.as_view(), name='user_suggestions'),
    
    # API quản lý kết nối
    path('api/connections/request/<int:user_id>/', ConnectionRequestView.as_view(), name='connection_request'),
    path('api/connections/accept/<int:connection_id>/', AcceptConnectionView.as_view(), name='accept_connection'),
    path('api/connections/decline/<int:connection_id>/', DeclineConnectionView.as_view(), name='decline_connection'),
    path('api/connections/remove/<int:user_id>/', RemoveConnectionView.as_view(), name='remove_connection'),
    path('api/connections/block/<int:user_id>/', BlockUserView.as_view(), name='block_user'),
    
    # API danh sách kết nối
    path('api/connections/pending/', PendingConnectionsView.as_view(), name='pending_connections'),
    path('api/connections/users/', ConnectedUsersView.as_view(), name='connected_users'),
    
    # API kiểm tra quyền chat
    path('api/chat/can-chat/<str:username>/', CanChatWithUserView.as_view(), name='can_chat_with_user'),
] 