from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets, generics
from .models import Playlist, Song, Album, Genre, Rating, Comment, SongPlayHistory, SearchHistory
from .serializers import (
    PlaylistSerializer, SongSerializer, AlbumSerializer, GenreSerializer, 
    RatingSerializer, CommentSerializer, SongPlayHistorySerializer, SearchHistorySerializer
)
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg, Sum
import random
from datetime import datetime, timedelta
import django.utils.timezone
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request
from .utils import get_audio_metadata, convert_audio_format, extract_synchronized_lyrics, import_synchronized_lyrics, normalize_audio, get_waveform_data
import os
from io import BytesIO

User = get_user_model()

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
        
        # Xử lý file âm thanh
        audio_file = request.FILES.get('audio_file')
        if audio_file:
            # Lưu file tạm để trích xuất metadata
            temp_file_path = f"/tmp/{audio_file.name}"
            with open(temp_file_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
            
            try:
                # Trích xuất metadata
                metadata = get_audio_metadata(temp_file_path)
                
                # Chuyển đổi sang MP3 nếu không phải MP3
                if not audio_file.name.lower().endswith('.mp3'):
                    converted_file = convert_audio_format(temp_file_path, output_format='mp3')
                    if converted_file:
                        # Thay thế file gốc bằng file MP3
                        with open(converted_file, 'rb') as f:
                            audio_content = f.read()
                        # Tạo tên file mới
                        name, _ = os.path.splitext(audio_file.name)
                        audio_file.name = f"{name}.mp3"
                        audio_file.file = BytesIO(audio_content)
                        audio_file.content_type = 'audio/mpeg'
                
                # Chuẩn hóa âm lượng nếu cần
                # normalized_file = normalize_audio(temp_file_path)
                # if normalized_file:
                #     with open(normalized_file, 'rb') as f:
                #         audio_content = f.read()
                #     audio_file.file = BytesIO(audio_content)
                
                # Bổ sung metadata vào data
                if not data.get('title') and metadata.get('title'):
                    data['title'] = metadata['title']
                if not data.get('artist') and metadata.get('artist'):
                    data['artist'] = metadata['artist']
                if not data.get('album') and metadata.get('album'):
                    data['album'] = metadata['album']
                if not data.get('genre') and metadata.get('genre'):
                    data['genre'] = metadata['genre']
                if not data.get('duration') and metadata.get('duration'):
                    data['duration'] = metadata['duration']
                if not data.get('lyrics') and metadata.get('lyrics'):
                    data['lyrics'] = metadata['lyrics']
            except Exception as e:
                print(f"Error processing audio file: {str(e)}")
            finally:
                # Xóa file tạm
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        
        serializer = SongSerializer(data=data)
        if serializer.is_valid():
            # Lưu song
            song = serializer.save()
            
            # Tạo dữ liệu waveform nếu cần
            # waveform = get_waveform_data(song.audio_file.path)
            # save waveform data...
            
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

# Thêm endpoint để xử lý lời bài hát đồng bộ
class SyncedLyricsView(APIView):
    """API xử lý lời bài hát đồng bộ theo thời gian"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, song_id, format=None):
        """Nhập lời bài hát đồng bộ"""
        # Kiểm tra quyền: chỉ admin hoặc người upload bài hát mới có thể cập nhật lời
        try:
            song = Song.objects.get(id=song_id)
            if not request.user.is_superuser and request.user != song.uploaded_by:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            lyrics_text = request.data.get('lyrics_text', '')
            if not lyrics_text:
                return Response({'error': 'No lyrics provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Import lời đồng bộ
            success = import_synchronized_lyrics(song_id, lyrics_text)
            if success:
                return Response({'status': 'Synced lyrics imported successfully'})
            else:
                return Response({'error': 'Failed to import synced lyrics'}, status=status.HTTP_400_BAD_REQUEST)
        except Song.DoesNotExist:
            return Response({'error': 'Song not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def get(self, request, song_id, format=None):
        """Lấy lời bài hát đồng bộ"""
        try:
            song = Song.objects.get(id=song_id)
            lyric_lines = song.lyric_lines.all()  # type: ignore
            
            # Format lời đồng bộ
            lyrics = []
            for line in lyric_lines:
                lyrics.append({
                    'timestamp': line.timestamp,
                    'formatted_time': line.format_timestamp(),
                    'text': line.text
                })
            
            return Response({
                'song_id': song_id,
                'song_title': song.title,
                'lyrics': lyrics
            })
        except Song.DoesNotExist:
            return Response({'error': 'Song not found'}, status=status.HTTP_404_NOT_FOUND)

# Admin Statistics and Analytics
class AdminStatisticsView(APIView):
    """View hiển thị thống kê tổng quan cho admin"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, format=None):
        """Lấy thống kê tổng quan về hệ thống âm nhạc"""
        # Thống kê tổng quan
        total_songs = Song.objects.count()
        total_playlists = Playlist.objects.count()
        total_users = User.objects.count()
        total_active_users = User.objects.filter(last_login__gte=django.utils.timezone.now() - timedelta(days=30)).count()
        
        # Tổng số lượt nghe
        total_plays = sum(Song.objects.values_list('play_count', flat=True))
        
        # Thống kê theo thể loại
        genre_stats = {}
        genres = set(Song.objects.values_list('genre', flat=True).distinct())
        for genre in genres:
            if genre:  # Một số bài hát có thể không có thể loại
                genre_count = Song.objects.filter(genre=genre).count()
                genre_plays = Song.objects.filter(genre=genre).aggregate(total=Sum('play_count'))['total'] or 0
                genre_stats[genre] = {
                    'song_count': genre_count,
                    'total_plays': genre_plays,
                    'avg_plays': round(genre_plays / genre_count, 2) if genre_count > 0 else 0
                }
        
        # Thống kê theo thời gian
        today = django.utils.timezone.now().date()
        month_plays = {}
        for i in range(30):
            date = today - timedelta(days=i)
            count = SongPlayHistory.objects.filter(played_at__date=date).count()
            month_plays[date.strftime('%Y-%m-%d')] = count
        
        # Top bài hát được nghe nhiều nhất
        top_songs = Song.objects.order_by('-play_count')[:10]
        top_songs_data = SongSerializer(top_songs, many=True).data
        
        # Top playlist được theo dõi nhiều nhất
        top_playlists = Playlist.objects.annotate(
            follower_count=Count('followers')
        ).order_by('-follower_count')[:10]
        top_playlists_data = PlaylistSerializer(top_playlists, many=True).data
        
        # Thống kê người dùng mới
        new_users_by_day = {}
        for i in range(30):
            date = today - timedelta(days=i)
            count = User.objects.filter(
                date_joined__year=date.year,
                date_joined__month=date.month,
                date_joined__day=date.day
            ).count()
            new_users_by_day[date.strftime('%Y-%m-%d')] = count
        
        return Response({
            'overview': {
                'total_songs': total_songs,
                'total_playlists': total_playlists,
                'total_users': total_users,
                'active_users': total_active_users,
                'total_plays': total_plays,
            },
            'genre_stats': genre_stats,
            'monthly_plays': month_plays,
            'top_songs': top_songs_data,
            'top_playlists': top_playlists_data,
            'new_users': new_users_by_day
        })


class AdminUserActivityView(APIView):
    """View hiển thị thông tin hoạt động người dùng cho admin"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, format=None):
        """Lấy thông tin hoạt động người dùng"""
        # Lấy user_id từ query param nếu có
        user_id = request.query_params.get('user_id')
        
        if user_id:
            # Thống kê cho một người dùng cụ thể
            try:
                user = User.objects.get(id=user_id)
                
                # Thông tin cơ bản
                user_info = {
                    'id': getattr(user, 'id', None),
                    'username': user.username,
                    'email': user.email,
                    'date_joined': user.date_joined,
                    'last_login': user.last_login,
                    'is_active': user.is_active,
                }
                
                # Lịch sử nghe nhạc
                play_history = SongPlayHistory.objects.filter(user=user).order_by('-played_at')[:100]
                play_history_data = []
                for history in play_history:
                    play_history_data.append({
                        'song_id': getattr(history.song, 'id', None),
                        'song_title': history.song.title,
                        'song_artist': history.song.artist,
                        'played_at': history.played_at,
                    })
                
                # Thống kê thể loại yêu thích
                favorite_genres = {}
                for history in SongPlayHistory.objects.filter(user=user):
                    genre = history.song.genre
                    if genre in favorite_genres:
                        favorite_genres[genre] += 1
                    else:
                        favorite_genres[genre] = 1
                
                # Sắp xếp thể loại theo số lượt nghe
                favorite_genres = dict(sorted(favorite_genres.items(), 
                                             key=lambda item: item[1], 
                                             reverse=True))
                
                # Playlist của người dùng
                playlists = Playlist.objects.filter(user=user)
                playlist_data = PlaylistSerializer(playlists, many=True).data
                
                # Bài hát yêu thích
                favorite_songs = user.favorite_songs.all()  # type: ignore
                favorite_songs_data = SongSerializer(favorite_songs, many=True).data
                
                # Thống kê hoạt động theo thời gian
                today = django.utils.timezone.now().date()
                daily_activity = {}
                for i in range(30):
                    date = today - timedelta(days=i)
                    count = SongPlayHistory.objects.filter(
                        user=user,
                        played_at__year=date.year,
                        played_at__month=date.month,
                        played_at__day=date.day
                    ).count()
                    daily_activity[date.strftime('%Y-%m-%d')] = count
                
                return Response({
                    'user_info': user_info,
                    'play_history': play_history_data,
                    'favorite_genres': favorite_genres,
                    'playlists': playlist_data,
                    'favorite_songs': favorite_songs_data,
                    'daily_activity': daily_activity,
                })
            
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        else:
            # Thống kê cho tất cả người dùng
            # Top người dùng nghe nhiều nhất
            top_listeners = User.objects.annotate(
                play_count=Count('play_history')
            ).order_by('-play_count')[:10]
            
            top_listeners_data = []
            for user in top_listeners:
                play_count = SongPlayHistory.objects.filter(user=user).count()
                top_listeners_data.append({
                    'id': getattr(user, 'id', None),
                    'username': user.username,
                    'play_count': play_count,
                    'playlist_count': Playlist.objects.filter(user=user).count(),
                    'date_joined': user.date_joined,
                    'last_login': user.last_login,
                })
            
            # Người dùng mới đăng ký
            new_users = User.objects.order_by('-date_joined')[:10]
            new_users_data = []
            for user in new_users:
                new_users_data.append({
                    'id': getattr(user, 'id', None),
                    'username': user.username,
                    'email': user.email,
                    'date_joined': user.date_joined,
                    'last_login': user.last_login,
                })
            
            # Người dùng hoạt động nhiều nhất gần đây
            active_users = User.objects.filter(
                last_login__gte=django.utils.timezone.now() - timedelta(days=7)
            ).annotate(
                recent_plays=Count('play_history', 
                                  filter=Q(play_history__played_at__gte=django.utils.timezone.now() - timedelta(days=7)))
            ).order_by('-recent_plays')[:10]
            
            active_users_data = []
            for user in active_users:
                active_users_data.append({
                    'id': getattr(user, 'id', None),
                    'username': user.username,
                    'recent_plays': getattr(user, 'recent_plays', 0),
                    'last_login': user.last_login,
                })
            
            return Response({
                'top_listeners': top_listeners_data,
                'new_users': new_users_data,
                'active_users': active_users_data,
            })

def play_song(request):
    # Đường dẫn file mp3 mẫu, có thể lấy từ database sau
    song_url = '/media/songs/2025/04/28/TinhNho-ThanhHien-5825173_XH1ISay.mp3'
    return render(request, 'play_song.html', {'song_url': song_url})