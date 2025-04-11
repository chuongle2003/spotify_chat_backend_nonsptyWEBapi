from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'songs', views.SongViewSet)
router.register(r'playlists', views.PlaylistViewSet)
router.register(r'albums', views.AlbumViewSet)
router.register(r'genres', views.GenreViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'ratings', views.RatingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Public URLs
    path('public/playlists/', views.PublicPlaylistView.as_view(), name='public-playlists'),
    path('public/search/', views.PublicSearchView.as_view(), name='public-search'),
    path('public/features/', views.PublicFeatures.as_view(), name='public-features'),
    
    # Authenticated URLs
    path('playlists/', views.UserPlaylistView.as_view(), name='user-playlists'),
    path('playlists/create/', views.CreatePlaylistView.as_view(), name='create-playlist'),
    path('features/basic/', views.BasicUserFeatures.as_view(), name='basic-features'),
    
    # Music player functionality
    path('upload/', views.SongUploadView.as_view(), name='song-upload'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('trending/', views.TrendingSongsView.as_view(), name='trending'),
    path('recommended/', views.RecommendedSongsView.as_view(), name='recommended'),
    path('library/', views.UserLibraryView.as_view(), name='user-library'),
]
