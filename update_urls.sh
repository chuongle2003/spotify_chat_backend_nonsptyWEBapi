#!/bin/bash

echo "=== Bắt đầu tối ưu cấu trúc URL ==="

# Tạo bản sao lưu trước khi thay đổi
mkdir -p backups
cp backend/urls.py backups/backend_urls.py.bak
cp music/urls.py backups/music_urls.py.bak
cp accounts/urls.py backups/accounts_urls.py.bak
cp chat/urls.py backups/chat_urls.py.bak

echo "=== Đã sao lưu các file URL gốc ==="

# 1. Tối ưu backend/urls.py
cat > backend/urls.py << 'EOF'
"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Cấu trúc URL rõ ràng, phân nhóm theo chức năng
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/music/', include('music.urls')),
    path('api/chat/', include('chat.urls')),
] 

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
EOF

echo "=== Đã tối ưu backend/urls.py ==="

# 2. Tối ưu music/urls.py bằng cách nhóm các endpoint lại
cat > music/urls.py << 'EOF'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ViewSet router
router = DefaultRouter()
router.register(r'songs', views.SongViewSet)
router.register(r'playlists', views.PlaylistViewSet)
router.register(r'albums', views.AlbumViewSet)
router.register(r'genres', views.GenreViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'ratings', views.RatingViewSet)

# Organize URLs by feature
urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # USER & AUTH - Authentication related endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # PUBLIC - Endpoints available without authentication
    path('public/', include([
        path('playlists/', views.PublicPlaylistView.as_view(), name='public-playlists'),
        path('search/', views.PublicSearchView.as_view(), name='public-search'),
        path('features/', views.PublicFeatures.as_view(), name='public-features'),
    ])),
    
    # PLAYLIST - Playlist management
    path('playlists/', views.UserPlaylistView.as_view(), name='user-playlists'),
    path('playlists/create/', views.CreatePlaylistView.as_view(), name='create-playlist'),
    
    # FEATURE MAPS - Feature discovery
    path('features/', include([
        path('basic/', views.BasicUserFeatures.as_view(), name='basic-features'),
    ])),
    
    # MUSIC PLAYER - Core music functionality
    path('upload/', views.SongUploadView.as_view(), name='song-upload'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('trending/', views.TrendingSongsView.as_view(), name='trending'),
    path('recommended/', views.RecommendedSongsView.as_view(), name='recommended'),
    path('library/', views.UserLibraryView.as_view(), name='user-library'),
]
EOF

echo "=== Đã tối ưu music/urls.py ==="

# 3. Tối ưu accounts/urls.py để phân nhóm endpoints
cat > accounts/urls.py << 'EOF'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # User management
    path('', include(router.urls)),
    
    # Additional endpoints can be organized here if needed:
    # path('profile/', views.ProfileView.as_view(), name='profile'),
    # path('settings/', views.SettingsView.as_view(), name='settings'),
]
EOF

echo "=== Đã tối ưu accounts/urls.py ==="

# 4. Tối ưu chat/urls.py để cấu trúc rõ ràng
cat > chat/urls.py << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    # Messages endpoints
    path('messages/', views.MessageListView.as_view(), name='message-list'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message-detail'),
    
    # Conversations endpoints
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:user_id>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
]

# WebSocket URLs - được xử lý riêng bởi routing.py
websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', views.ChatConsumer.as_asgi()),
]
EOF

echo "=== Đã tối ưu chat/urls.py ==="

echo "=== Tối ưu hoàn tất! ==="
echo "Bạn có thể cần chỉnh sửa thêm nếu đường dẫn import không đúng."
echo "Để hoàn tác thay đổi: cp backups/*_urls.py.bak các thư mục tương ứng" 