from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts import views

# Router cho các ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # API danh sách người dùng
    path('api/users/', views.UserListView.as_view(), name='user_list'),
    path('api/users/suggestions/', views.UserSuggestionsView.as_view(), name='user_suggestions'),
    
    # API quản lý kết nối
    path('api/connections/request/<int:user_id>/', views.ConnectionRequestView.as_view(), name='connection_request'),
    path('api/connections/accept/<int:connection_id>/', views.AcceptConnectionView.as_view(), name='accept_connection'),
    path('api/connections/decline/<int:connection_id>/', views.DeclineConnectionView.as_view(), name='decline_connection'),
    path('api/connections/remove/<int:user_id>/', views.RemoveConnectionView.as_view(), name='remove_connection'),
    path('api/connections/block/<int:user_id>/', views.BlockUserView.as_view(), name='block_user'),
    
    # API danh sách kết nối
    path('api/connections/pending/', views.PendingConnectionsView.as_view(), name='pending_connections'),
    path('api/connections/users/', views.ConnectedUsersView.as_view(), name='connected_users'),
    
    # API kiểm tra quyền chat
    path('api/chat/can-chat/<str:username>/', views.CanChatWithUserView.as_view(), name='can_chat_with_user'),
] 