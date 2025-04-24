from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'admin/users', views.AdminViewSet)
router.register(r'user-management', views.UserManagementViewSet)
# Content và Playlist management sẽ được đăng ký trong ứng dụng tương ứng

urlpatterns = [
    # User management
    path('', include(router.urls)),
    
    # Authentication
    path('auth/', include([
        path('register/', views.RegisterView.as_view(), name='register'),
        path('logout/', views.LogoutView.as_view(), name='logout'),
    ])),
    
    # Public endpoints không cần xác thực
    path('public/users/', views.PublicUserListView.as_view(), name='public-users'),
    
    # Additional endpoints can be organized here if needed:
    # path('profile/', views.ProfileView.as_view(), name='profile'),
    # path('settings/', views.SettingsView.as_view(), name='settings'),
] 