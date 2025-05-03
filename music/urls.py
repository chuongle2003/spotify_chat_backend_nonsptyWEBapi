from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import (SearchHistoryView, SongRecommendationView)


router = DefaultRouter()
router.register(r'songs', views.SongViewSet)
router.register(r'playlists', views.PlaylistViewSet)
router.register(r'albums', views.AlbumViewSet)
router.register(r'genres', views.GenreViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'ratings', views.RatingViewSet)
router.register(r'artists', views.ArtistViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Trang chủ và khám phá nhạc
    path('home/', views.HomePageView.as_view(), name='home'),
    path('albums/new/', views.NewAlbumsView.as_view(), name='albums-new'),
    path('playlists/featured/', views.FeaturedPlaylistsView.as_view(), name='featured-playlists'),
    
    # Public URLs
    path('public/playlists/', views.PublicPlaylistView.as_view(), name='public-playlists'),
    path('public/search/', views.PublicSearchView.as_view(), name='public-search'),
    path('public/features/', views.PublicFeatures.as_view(), name='public-features'),
    
    # Authenticated URLs
    path('playlists/', views.UserPlaylistView.as_view(), name='user-playlists'),
    path('playlists/create/', views.CreatePlaylistView.as_view(), name='create-playlist'),
    path('features/basic/', views.BasicUserFeatures.as_view(), name='basic-features'),
    
    # Playlist - Extra endpoints
    path('playlists/<int:pk>/update-cover/', views.PlaylistViewSet.as_view({'post': 'update_cover_image'}), name='playlist-update-cover'),
    path('playlists/<int:pk>/toggle-privacy/', views.PlaylistViewSet.as_view({'post': 'toggle_privacy'}), name='playlist-toggle-privacy'),
    path('playlists/<int:pk>/followers/', views.PlaylistViewSet.as_view({'get': 'followers'}), name='playlist-followers'),
    
    # Music player functionality
    path('upload/', views.SongUploadView.as_view(), name='song-upload'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('trending/', views.TrendingSongsView.as_view(), name='trending'),
    path('recommended/', views.RecommendedSongsView.as_view(), name='recommended'),
    path('library/', views.UserLibraryView.as_view(), name='user-library'),
    
    # Queue và Player
    path('queue/', views.QueueView.as_view(), name='queue'),
    path('queue/add/', views.AddToQueueView.as_view(), name='add-to-queue'),
    path('queue/remove/<int:position>/', views.RemoveFromQueueView.as_view(), name='remove-from-queue'),
    path('queue/clear/', views.ClearQueueView.as_view(), name='clear-queue'),
    
    # User status
    path('status/', views.UserStatusView.as_view(), name='user-status'),
    
    # Chat và chia sẻ nhạc
    path('messages/', views.MessageListView.as_view(), name='messages'),
    path('messages/send/', views.SendMessageView.as_view(), name='send-message'),
    path('share/song/<int:song_id>/', views.ShareSongView.as_view(), name='share-song'),
    path('share/playlist/<int:playlist_id>/', views.SharePlaylistView.as_view(), name='share-playlist'),
    
    # Thống kê và xu hướng cá nhân
    path('statistics/', views.UserStatisticsView.as_view(), name='user-statistics'),
    path('trends/personal/', views.PersonalTrendsView.as_view(), name='personal-trends'),
    
    # Đề xuất cá nhân hóa
    path('recommendations/', views.RecommendationsView.as_view(), name='recommendations'),
    path('recommendations/liked/', views.LikedBasedRecommendationsView.as_view(), name='liked-recommendations'),
    path('recommendations/may-like/', views.YouMayLikeView.as_view(), name='may-like'),
    
    # Lịch sử
    path('history/', views.PlayHistoryView.as_view(), name='play-history'),
    path('history/search/', views.SearchHistoryView.as_view(), name='search-history'),
    
    # Lyrics management
    path('songs/<int:song_id>/lyrics/synced/', views.SyncedLyricsView.as_view(), name='synced-lyrics'),
    path('play/', views.play_song, name='play_song'),
    path('search-history/', SearchHistoryView.as_view(), name='search-history'),
    path('search-history/delete/', SearchHistoryView.as_view(), name='delete-search-history'),
    path('recommendations/songs/', SongRecommendationView.as_view(), name='song-recommendations'),
]
if settings.DEBUG:
      urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)