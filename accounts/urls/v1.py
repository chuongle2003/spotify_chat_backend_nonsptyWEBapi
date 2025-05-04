from django.urls import path
from rest_framework.routers import DefaultRouter
from accounts import views

app_name = 'accounts_v1'

# Sử dụng router cho các ViewSets
router = DefaultRouter()
router.register('users', views.UserViewSet, basename='user')
router.register('admin/users', views.AdminViewSet, basename='admin-user')

urlpatterns = [
    # Danh sách người dùng và quản lý tài khoản
    path('user-list/', views.UserListView.as_view(), name='user-list'),
    path('user-search/', views.UserSearchView.as_view(), name='user-search'),
    path('user-suggestions/', views.UserSuggestionsView.as_view(), name='user-suggestions'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Quên mật khẩu và đặt lại mật khẩu
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.VerifyPasswordResetTokenView.as_view(), name='reset-password'),
    
    # Xem và quản lý người theo dõi
    path('following/', views.UserFollowingListView.as_view(), name='following-list'),
    path('followers/', views.UserFollowersListView.as_view(), name='followers-list'),
    path('follow/<int:user_id>/', views.FollowUserView.as_view(), name='follow-user'),
    path('unfollow/<int:user_id>/', views.UnfollowUserView.as_view(), name='unfollow-user'),
    
    # API quản lý kết nối
    path('connections/', views.ConnectedUsersView.as_view(), name='connected-users'),
    path('connections/pending/', views.PendingConnectionsView.as_view(), name='pending-connections'),
    path('connections/request/<int:user_id>/', views.ConnectionRequestView.as_view(), name='connection-request'),
    path('connections/accept/<int:connection_id>/', views.AcceptConnectionView.as_view(), name='accept-connection'),
    path('connections/decline/<int:connection_id>/', views.DeclineConnectionView.as_view(), name='decline-connection'),
    path('connections/remove/<int:user_id>/', views.RemoveConnectionView.as_view(), name='remove-connection'),
    path('connections/block/<int:user_id>/', views.BlockUserView.as_view(), name='block-user'),
    
    # Kiểm tra quyền chat
    path('chat-permission/<str:username>/', views.CanChatWithUserView.as_view(), name='can-chat-with-user'),
]

# Thêm các URL từ router
urlpatterns += router.urls 