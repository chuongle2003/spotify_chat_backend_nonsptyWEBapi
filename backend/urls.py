"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from accounts.views import CustomTokenObtainPairView

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls.legacy')),
    path('api/chat/', include('chat.urls.legacy')),
    path('api/music/', include('music.urls.legacy')),
    path('api/ai/', include('ai_assistant.urls.legacy')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

