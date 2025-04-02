from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets, generics
from .models import Playlist, Song, Album, Genre, Rating, Comment, SongPlayHistory, SearchHistory
from .serializers import (
    PlaylistSerializer, SongSerializer, AlbumSerializer, GenreSerializer, 
    RatingSerializer, CommentSerializer, UserSerializer, UserProfileSerializer,
    SongPlayHistorySerializer, SearchHistorySerializer
)
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
import random
from datetime import datetime, timedelta
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request

User = get_user_model()

# Các view không liên quan đến Spotify

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        password = self.request.data.get('password')  # type: ignore
        user = serializer.save()
        user.set_password(password)
        user.save()
        return user

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

# Các view cơ bản
class PublicPlaylistView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        playlists = Playlist.objects.filter(is_public=True)
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)

class UserPlaylistView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        playlists = Playlist.objects.filter(user=request.user)
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)

class PublicFeatures(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'public_playlists': reverse('public-playlists'),
            'search': reverse('public-search'),
            'top_songs': reverse('trending'),
        })

class PublicSearchView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.GET.get('q', '')
        songs = Song.objects.filter(
            Q(title__icontains=query) | 
            Q(artist__icontains=query) | 
            Q(album__icontains=query)
        )
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)

class BasicUserFeatures(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'my_playlists': reverse('user-playlists'),
            'create_playlist': reverse('create-playlist'),
            'profile': reverse('user-profile'),
            'upload': reverse('song-upload'),
            'library': reverse('user-library'),
            'search': reverse('search'),
        })

class CreatePlaylistView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PlaylistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

# ViewSets
class SongViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Song"""
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def play(self, request, pk=None):
        """Ghi lại lượt phát của bài hát"""
        song = self.get_object()
        song.play_count += 1
        song.save()
        
        # Lưu lịch sử phát
        SongPlayHistory.objects.create(
            user=request.user,
            song=song,
            played_at=datetime.now()
        )
        
        return Response({'status': 'play logged'})
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Yêu thích bài hát"""
        song = self.get_object()
        user = request.user
        
        if song in user.favorite_songs.all():
            user.favorite_songs.remove(song)
            song.likes_count = max(0, song.likes_count - 1)
            song.save()
            return Response({'status': 'unliked'})
        else:
            user.favorite_songs.add(song)
            song.likes_count += 1
            song.save()
            return Response({'status': 'liked'})
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Lấy danh sách bài hát trending dựa trên lượt play gần đây"""
        # Lấy bài hát có nhiều lượt phát nhất trong 7 ngày qua
        last_week = datetime.now() - timedelta(days=7)
        trending_songs = Song.objects.filter(
            songplayhistory__played_at__gte=last_week
        ).annotate(
            recent_plays=Count('songplayhistory')
        ).order_by('-recent_plays', '-likes_count')[:10]
        
        serializer = self.get_serializer(trending_songs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Đề xuất bài hát dựa trên thể loại yêu thích của người dùng"""
        user = request.user
        
        # Nếu user chưa nghe bài nào, đề xuất bài phổ biến
        if not user.favorite_songs.exists() and not SongPlayHistory.objects.filter(user=user).exists():
            popular_songs = Song.objects.order_by('-play_count', '-likes_count')[:10]
            serializer = self.get_serializer(popular_songs, many=True)
            return Response(serializer.data)
        
        # Tìm thể loại nghe nhiều nhất
        favorite_genres = set()
        
        # Từ bài hát yêu thích
        for song in user.favorite_songs.all():
            favorite_genres.add(song.genre)
        
        # Từ lịch sử nghe
        played_songs = SongPlayHistory.objects.filter(user=user).select_related('song')
        for play in played_songs:
            favorite_genres.add(play.song.genre)
        
        # Đề xuất bài hát cùng thể loại mà user chưa nghe
        played_song_ids = played_songs.values_list('song_id', flat=True)
        fav_song_ids = user.favorite_songs.values_list('id', flat=True)
        
        recommended_songs = Song.objects.filter(
            genre__in=favorite_genres
        ).exclude(
            id__in=list(played_song_ids) + list(fav_song_ids)
        ).order_by('-likes_count')[:10]
        
        # Nếu không đủ 10 bài, bổ sung thêm bài phổ biến
        if recommended_songs.count() < 10:
            excluded_ids = list(recommended_songs.values_list('id', flat=True)) + list(played_song_ids) + list(fav_song_ids)
            more_songs = Song.objects.exclude(id__in=excluded_ids).order_by('-play_count')[:10-recommended_songs.count()]
            recommended_songs = list(recommended_songs) + list(more_songs)
        
        serializer = self.get_serializer(recommended_songs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Tìm kiếm bài hát"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        songs = Song.objects.filter(
            Q(title__icontains=query) | 
            Q(artist__icontains=query) | 
            Q(album__icontains=query) |
            Q(genre__icontains=query)
        )
        
        serializer = self.get_serializer(songs, many=True)
        return Response(serializer.data)

class SongUploadView(APIView):
    """Upload bài hát mới"""
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        """Xử lý upload file audio"""
        # Thêm user vào request data
        data = request.data.copy()
        data['uploaded_by'] = request.user.id
        
        serializer = SongSerializer(data=data)
        if serializer.is_valid():
            # Lưu song
            song = serializer.save()
            
            # Xử lý audio file nếu cần (có thể thêm code xử lý file ở đây)
            # from .utils import process_audio_file
            # process_audio_file(song.audio_file.path)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlaylistViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Playlist"""
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        """Lọc playlist: chỉ hiển thị playlist công khai hoặc của user đang đăng nhập"""
        user = self.request.user
        if user.is_authenticated:
            return Playlist.objects.filter(
                Q(is_public=True) | Q(user=user)
            )
        return Playlist.objects.filter(is_public=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_song(self, request, pk=None):
        """Thêm bài hát vào playlist"""
        playlist = self.get_object()
        
        # Kiểm tra quyền chỉnh sửa playlist
        if playlist.user != request.user:
            return Response({'error': 'You do not have permission to edit this playlist'}, 
                          status=status.HTTP_403_FORBIDDEN)
            
        song_id = request.data.get('song_id')
        if not song_id:
            return Response({'error': 'Song ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            song = Song.objects.get(id=song_id)
            playlist.songs.add(song)
            return Response({'status': 'song added to playlist'})
        except Song.DoesNotExist:
            return Response({'error': 'Song not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_song(self, request, pk=None):
        """Xóa bài hát khỏi playlist"""
        playlist = self.get_object()
        
        # Kiểm tra quyền chỉnh sửa playlist
        if playlist.user != request.user:
            return Response({'error': 'You do not have permission to edit this playlist'}, 
                          status=status.HTTP_403_FORBIDDEN)
            
        song_id = request.data.get('song_id')
        if not song_id:
            return Response({'error': 'Song ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            song = Song.objects.get(id=song_id)
            playlist.songs.remove(song)
            return Response({'status': 'song removed from playlist'})
        except Song.DoesNotExist:
            return Response({'error': 'Song not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Theo dõi playlist"""
        playlist = self.get_object()
        user = request.user
        
        if playlist.followers.filter(id=user.id).exists():
            return Response({'error': 'You are already following this playlist'}, 
                          status=status.HTTP_400_BAD_REQUEST)
            
        playlist.followers.add(user)
        return Response({'status': 'playlist followed'})
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """Bỏ theo dõi playlist"""
        playlist = self.get_object()
        user = request.user
        
        playlist.followers.remove(user)
        return Response({'status': 'playlist unfollowed'})

class AlbumViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Album"""
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    
    @action(detail=True, methods=['get'])
    def songs(self, request, pk=None):
        """Lấy danh sách bài hát trong album"""
        album = self.get_object()
        songs = Song.objects.filter(album=album.title)
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)

class GenreViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Genre"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    
    @action(detail=True, methods=['get'])
    def songs(self, request, pk=None):
        """Lấy danh sách bài hát theo thể loại"""
        genre = self.get_object()
        songs = Song.objects.filter(genre=genre.name)
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Comment"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RatingViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Rating"""
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserLibraryView(APIView):
    """Lấy thư viện nhạc của người dùng"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Lấy bài hát yêu thích
        favorite_songs = user.favorite_songs.all()
        favorite_serializer = SongSerializer(favorite_songs, many=True)
        
        # Lấy playlist
        playlists = Playlist.objects.filter(user=user)
        playlist_serializer = PlaylistSerializer(playlists, many=True)
        
        # Lấy playlist đang theo dõi
        followed_playlists = user.followed_playlists.all()
        followed_serializer = PlaylistSerializer(followed_playlists, many=True)
        
        # Lấy lịch sử nghe gần đây
        recent_history = SongPlayHistory.objects.filter(
            user=user
        ).order_by('-played_at')[:20]
        
        recent_songs = []
        song_ids = set()
        
        # Chỉ lấy mỗi bài hát một lần trong lịch sử
        for history in recent_history:
            if history.song.pk not in song_ids:  # Sử dụng pk thay vì id để tránh lỗi
                recent_songs.append(history.song)
                song_ids.add(history.song.pk)
        
        recent_serializer = SongSerializer(recent_songs, many=True)
        
        return Response({
            'favorite_songs': favorite_serializer.data,
            'playlists': playlist_serializer.data,
            'followed_playlists': followed_serializer.data,
            'recently_played': recent_serializer.data
        })

class TrendingSongsView(APIView):
    """Lấy bài hát xu hướng"""
    
    def get(self, request, format=None):
        # Lấy top 10 bài hát có nhiều lượt phát nhất
        trending_songs = Song.objects.order_by('-play_count')[:10]
        serializer = SongSerializer(trending_songs, many=True)
        return Response(serializer.data)

class RecommendedSongsView(APIView):
    """Bài hát gợi ý cho user hiện tại"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Logic gợi ý đơn giản: lấy các bài hát cùng thể loại với bài hát yêu thích
        favorite_genres = set()
        for song in user.favorite_songs.all():
            favorite_genres.add(song.genre)
        
        # Nếu chưa có bài hát yêu thích, lấy từ lịch sử nghe
        if not favorite_genres:
            for history in SongPlayHistory.objects.filter(user=user):
                favorite_genres.add(history.song.genre)
        
        # Nếu vẫn không có, trả về bài hát phổ biến
        if not favorite_genres:
            popular_songs = Song.objects.order_by('-play_count')[:10]
            serializer = SongSerializer(popular_songs, many=True)
            return Response(serializer.data)
        
        # Lấy bài hát cùng thể loại yêu thích mà user chưa nghe
        listened_songs = SongPlayHistory.objects.filter(user=user).values_list('song_id', flat=True)
        
        recommended = Song.objects.filter(
            genre__in=favorite_genres
        ).exclude(
            id__in=list(listened_songs)
        ).order_by('?')[:10]  # Random selection
        
        serializer = SongSerializer(recommended, many=True)
        return Response(serializer.data)

class SearchView(APIView):
    """Tìm kiếm bài hát, album, artist, playlist"""
    
    def get(self, request, format=None):
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Tìm bài hát
        songs = Song.objects.filter(
            Q(title__icontains=query) | 
            Q(artist__icontains=query) | 
            Q(album__icontains=query)
        )
        song_serializer = SongSerializer(songs, many=True)
        
        # Tìm playlist (chỉ playlist công khai)
        playlists = Playlist.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query),
            is_public=True
        )
        playlist_serializer = PlaylistSerializer(playlists, many=True)
        
        # Tìm album
        albums = Album.objects.filter(
            Q(title__icontains=query) | 
            Q(artist__icontains=query)
        )
        album_serializer = AlbumSerializer(albums, many=True)
        
        # Lưu lịch sử tìm kiếm
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                user=request.user,
                query=query
            )
        
        return Response({
            'songs': song_serializer.data,
            'playlists': playlist_serializer.data,
            'albums': album_serializer.data
        })