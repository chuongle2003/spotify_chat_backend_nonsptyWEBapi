from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Đăng ký các viewsets với router để tạo URLs tự động
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'admin/users', views.AdminViewSet)

urlpatterns = [
    # Bao gồm tất cả router URLs
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/', include([
        path('register/', views.RegisterView.as_view(), name='register'),
        # LogoutView đã được chuyển lên /api/v1/auth/logout/ 
        # nên không còn khai báo ở đây nữa
        path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
        path('verify-reset-token/', views.VerifyPasswordResetTokenView.as_view(), name='verify-reset-token'),
    ])),
    
    # Public endpoints - nhóm lại các endpoints công khai
    path('public/', include([
        path('users/', views.PublicUserListView.as_view(), name='public-users'),
    ])),
    
    # Thêm không gian cho các endpoints tương lai
    # path('profile/', include([
    #     path('settings/', views.ProfileSettingsView.as_view(), name='profile-settings'),
    #     path('preferences/', views.ProfilePreferencesView.as_view(), name='profile-preferences'),
    # ])),
] 