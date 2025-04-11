from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # User management
    path('', include(router.urls)),
    
    # Public endpoints không cần xác thực
    path('public/users/', views.PublicUserListView.as_view(), name='public-users'),
    
    # Additional endpoints can be organized here if needed:
    # path('profile/', views.ProfileView.as_view(), name='profile'),
    # path('settings/', views.SettingsView.as_view(), name='settings'),
] 