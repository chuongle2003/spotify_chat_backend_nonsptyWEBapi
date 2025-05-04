"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from accounts.views import LogoutView, CustomTokenObtainPairView  # Import CustomTokenObtainPairView
from ai_assistant.views import APIDocumentationView
from django.http import HttpResponsePermanentRedirect
from rest_framework.views import APIView
from rest_framework.response import Response

# Class xử lý thông báo API deprecation
class DeprecatedAPIWarningView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({
            "warning": "Đường dẫn API hiện tại đã cũ và sẽ bị loại bỏ trong các phiên bản tương lai. Vui lòng sử dụng /api/v1/ cho tất cả các request mới.",
            "new_url_prefix": "/api/v1/"
        })

# Định nghĩa API v1 patterns
api_v1_patterns = [
    # Auth endpoints - Tập trung endpoints xác thực
    path('auth/', include([
        path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('logout/', LogoutView.as_view(), name='logout'),
    ])),
    
    # Module endpoints
    path('accounts/', include('accounts.urls')),
    path('music/', include('music.urls')),
    path('chat/', include('chat.urls')),
]

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include(api_v1_patterns)),
    
    # API deprecation warning
    path('api/deprecation-warning/', DeprecatedAPIWarningView.as_view(), name='api-deprecation-warning'),
    
    # Legacy support - để duy trì tương thích ngược
    path('api/', include([
        # Thông báo deprecation
        path('', DeprecatedAPIWarningView.as_view(), name='api-deprecated-root'),
        
        # JWT Auth theo cấu trúc cũ
        path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair_legacy'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh_legacy'),
        
        # Các modules
        path('accounts/', include('accounts.urls')),
        path('music/', include('music.urls')),
        path('chat/', include('chat.urls')),
    ])),
    
    # API Documentation
    path('api/documentation/', APIDocumentationView.as_view(permission_classes=[]), name='api-documentation'),
    
    # API Documentation (Swagger/OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', include([
        path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ])),
    
    # AI Assistant Endpoints
    path('api/v1/ai/', include('ai_assistant.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

