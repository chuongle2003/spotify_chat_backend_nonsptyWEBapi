from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets, generics, filters
from .models import (
    Playlist, Song, Album, Genre, Rating, Comment, SongPlayHistory, 
    SearchHistory, Artist, Queue, QueueItem, UserStatus, LyricLine, Message, UserRecommendation,
    CollaboratorRole, PlaylistEditHistory, OfflineDownload
)
from .serializers import (
    PlaylistSerializer, SongSerializer, AlbumSerializer, GenreSerializer, 
    RatingSerializer, CommentSerializer, SongPlayHistorySerializer,
    SearchHistorySerializer, PlaylistDetailSerializer, SongDetailSerializer,
    AlbumDetailSerializer, GenreDetailSerializer, ArtistSerializer,
    QueueSerializer, UserStatusSerializer, LyricLineSerializer, MessageSerializer,
    UserBasicSerializer, CollaboratorRoleSerializer, CollaboratorRoleCreateSerializer,
    PlaylistEditHistorySerializer, OfflineDownloadSerializer
)
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg, Sum, F
import random
from datetime import datetime, timedelta
import django.utils.timezone
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request
from .utils import get_audio_metadata, convert_audio_format, extract_synchronized_lyrics, import_synchronized_lyrics, normalize_audio, get_waveform_data, generate_song_recommendations, download_song_for_offline, verify_offline_song, get_offline_song_metadata
import os
from io import BytesIO
from django.conf import settings

User = get_user_model()

# API cho trang chủ - khám phá nhạc
class HomePageView(APIView):
    """API cho trang chủ - khám phá nhạc, không yêu cầu đăng nhập"""
    permission_classes = [AllowAny]
    
    def get(self, request, format=None):
        # Lấy bài hát nổi bật theo thể loại
        genres = Genre.objects.all()[:6]  # Lấy 6 thể loại
        featured_by_genre = {}
        
        for genre in genres:
            top_songs = Song.objects.filter(genre=genre.name).order_by('-play_count')[:5]
            featured_by_genre[genre.name] = SongSerializer(top_songs, many=True).data
        
        # Album mới phát hành
        one_month_ago = datetime.now().date() - timedelta(days=30)
        new_albums = Album.objects.filter(release_date__gte=one_month_ago).order_by('-release_date')[:8]
        
        # Playlist được yêu thích
        popular_playlists = Playlist.objects.filter(is_public=True).annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')[:8]
        
        # Top bài hát được nghe nhiều
        top_songs = Song.objects.order_by('-play_count')[:10]
        
        return Response({
            'featured_by_genre': featured_by_genre,
            'new_albums': AlbumSerializer(new_albums, many=True).data,
            'popular_playlists': PlaylistSerializer(popular_playlists, many=True).data,
            'top_songs': SongSerializer(top_songs, many=True).data
        })

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
            'home': reverse('home'),
            'albums_new': reverse('albums-new'),
            'featured_playlists': reverse('featured-playlists'),
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
            'recommended': reverse('recommended'),
            'trending': reverse('trending'),
            'queue': reverse('queue'),
            'statistics': reverse('user-statistics'),
            'trends': reverse('personal-trends'),
            'offline': reverse('offline-downloads'),
            'download': reverse('offline-download-request')
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
    
    def get_permissions(self):
        """
        Cho phép người dùng chưa đăng nhập xem thông tin bài hát,
        nhưng chỉ người dùng đã đăng nhập mới có thể thao tác.
        """
        if self.action in ['list', 'retrieve', 'search', 'trending']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SongDetailSerializer
        return SongSerializer
    
    def get_serializer(self, *args, **kwargs):
        """Đảm bảo request context được truyền vào serializer"""
        kwargs['context'] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)
    
    def get_serializer_context(self):
        """Thêm request vào context của serializer"""
        context = super().get_serializer_context()
        return context
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
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
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def trending(self, request):
        """Lấy bài hát xu hướng (trending) dựa trên số lượt phát gần đây"""
        # Số ngày để xác định xu hướng
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))
        genre = request.query_params.get('genre', None)
        
        # Tính khoảng thời gian
        start_date = django.utils.timezone.now() - timedelta(days=days)
        
        try:
            # Base query
            query = Song.objects.filter(
                play_history__played_at__gte=start_date
            )
            
            # Lọc theo thể loại nếu có
            if genre:
                query = query.filter(genre=genre)
            
            # Tính toán số lượt phát gần đây và sắp xếp
            trending_songs = query.annotate(
                recent_plays=Count('play_history')
            ).order_by('-recent_plays', '-likes_count')[:limit]
        
            # Nếu không có bài hát trending, trả về dựa trên likes_count và play_count
            if not trending_songs.exists():
                trending_songs = Song.objects.all().order_by('-likes_count', '-play_count')[:limit]

            # Lấy thông tin chi tiết
            serializer = self.get_serializer(trending_songs, many=True)
            
            # Thêm metadata về số lượt phát gần đây cho mỗi bài hát
            result_data = serializer.data
            for i, song in enumerate(trending_songs):
                result_data[i]['recent_plays'] = SongPlayHistory.objects.filter(
                    song=song, 
                    played_at__gte=start_date
                ).count()
            
            return Response({
                'trending_period_days': days,
                'results': result_data
            })
        
        except Exception as e:
            # Xử lý lỗi và trả về danh sách bài hát phổ biến thay thế
            trending_songs = Song.objects.all().order_by('-likes_count', '-play_count')[:limit]
            serializer = self.get_serializer(trending_songs, many=True)
            
            return Response({
                'trending_period_days': days,
                'results': serializer.data,
                'note': 'Showing popular songs due to an error with trending data'
            })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
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
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def search(self, request):
        """Tìm kiếm bài hát"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Cần cung cấp từ khóa tìm kiếm'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Tìm kiếm theo title, artist, album, genre
        songs = Song.objects.filter(
            Q(title__icontains=query) | 
            Q(artist__icontains=query) | 
            Q(album__icontains=query) |
            Q(genre__icontains=query)
        )
        
        # Bộ lọc thêm
        genre = request.query_params.get('genre', None)
        artist = request.query_params.get('artist', None)
        
        if genre:
            songs = songs.filter(genre=genre)
        
        if artist:
            songs = songs.filter(artist=artist)
        
        # Sắp xếp
        sort_by = request.query_params.get('sort', 'title')
        if sort_by == 'title':
            songs = songs.order_by('title')
        elif sort_by == 'artist':
            songs = songs.order_by('artist')
        elif sort_by == 'release_date':
            songs = songs.order_by('-release_date')
        
        # Phân trang
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = self.get_serializer(songs[start:end], many=True)
        
        # Lưu lịch sử tìm kiếm nếu đã đăng nhập
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                user=request.user,
                query=query
            )
        
        return Response({
            'total': songs.count(),
            'page': page, 
            'page_size': page_size,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def filter(self, request):
        """Lọc bài hát theo nhiều tiêu chí"""
        songs = Song.objects.all()
        
        # Lọc theo thể loại
        genre = request.query_params.get('genre', None)
        if genre:
            songs = songs.filter(genre=genre)
        
        # Lọc theo nghệ sĩ
        artist = request.query_params.get('artist', None)
        if artist:
            songs = songs.filter(artist=artist)
            
        # Lọc theo album
        album = request.query_params.get('album', None)
        if album:
            songs = songs.filter(album=album)
        
        # Sắp xếp
        sort_by = request.query_params.get('sort', 'title')
        if sort_by == 'title':
            songs = songs.order_by('title')
        elif sort_by == 'artist':
            songs = songs.order_by('artist')
        elif sort_by == 'release_date':
            songs = songs.order_by('-release_date')
        elif sort_by == 'popularity':
            songs = songs.order_by('-play_count')
        
        # Phân trang
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = self.get_serializer(songs[start:end], many=True)
        
        return Response({
            'total': songs.count(),
            'page': page, 
            'page_size': page_size,
            'results': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rate(self, request, pk=None):
        """Đánh giá bài hát"""
        song = self.get_object()
        user = request.user
        
        # Kiểm tra rating hợp lệ
        rating_value = request.data.get('rating')
        if not rating_value or not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
            return Response({'error': 'Rating must be an integer between 1 and 5'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Kiểm tra xem user đã đánh giá trước đó chưa
        try:
            # Nếu tìm thấy, cập nhật đánh giá
            rating = Rating.objects.get(user=user, song=song)
            rating.rating = rating_value
            rating.save()
            serializer = RatingSerializer(rating)
            return Response({
                'status': 'rating updated',
                'rating': serializer.data
            })
        except Rating.DoesNotExist:
            # Nếu chưa đánh giá, tạo mới
            rating = Rating.objects.create(
                user=user,
                song=song,
                rating=rating_value
            )
            serializer = RatingSerializer(rating)
            return Response({
                'status': 'rating created',
                'rating': serializer.data
            })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def comment(self, request, pk=None):
        """Bình luận về bài hát"""
        song = self.get_object()
        user = request.user
        
        # Kiểm tra nội dung bình luận
        content = request.data.get('content')
        if not content or not content.strip():
            return Response({'error': 'Comment content is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Kiểm tra xem có phải là reply cho comment khác không
        parent_id = request.data.get('parent_id')
        parent = None
        
        if parent_id:
            try:
                parent = Comment.objects.get(id=parent_id, song=song)
            except Comment.DoesNotExist:
                return Response({'error': 'Parent comment not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
        
        # Tạo comment mới
        comment = Comment.objects.create(
            user=user,
            song=song,
            content=content,
            parent=parent
        )
        
        serializer = CommentSerializer(comment)
        return Response({
            'status': 'comment created',
            'comment': serializer.data
        })

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

    def get_permissions(self):
        """
        Cho phép người dùng chưa đăng nhập xem playlist công khai,
        nhưng chỉ người dùng đã đăng nhập mới có thể thao tác.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Lọc playlist: chỉ hiển thị playlist công khai hoặc của user đang đăng nhập"""
        user = self.request.user
        if user.is_authenticated:
            return Playlist.objects.filter(
                Q(is_public=True) | Q(user=user)
            )
        return Playlist.objects.filter(is_public=True)
    
    def get_serializer_class(self):
        """Sử dụng serializer khác nhau tùy theo action"""
        if self.action == 'retrieve':
            return PlaylistDetailSerializer
        return PlaylistSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """
        Chỉ cho phép xem playlist private nếu là chủ sở hữu
        """
        instance = self.get_object()
        if not instance.is_public and instance.user != request.user:
            return Response(
                {'error': 'Bạn không có quyền xem playlist riêng tư này'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Gán user hiện tại làm chủ sở hữu khi tạo playlist"""
        serializer.save(user=self.request.user)
        self.request._request.session['message'] = 'Đã tạo playlist thành công!'
    
    def create(self, request, *args, **kwargs):
        """Tạo playlist mới với validate dữ liệu"""
        # Kiểm tra tên playlist
        if not request.data.get('name'):
            return Response(
                {'error': 'Tên playlist không được để trống'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Giới hạn số lượng playlist mỗi user
        user_playlists_count = Playlist.objects.filter(user=request.user).count()
        if user_playlists_count >= 50:  # Giới hạn tối đa 50 playlist/user
            return Response(
                {'error': 'Bạn đã đạt giới hạn tối đa 50 playlist'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Chỉ cho phép chủ sở hữu cập nhật thông tin playlist"""
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response(
                {'error': 'Bạn không có quyền chỉnh sửa playlist này'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Chỉ cho phép chủ sở hữu xóa playlist"""
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response(
                {'error': 'Bạn không có quyền xóa playlist này'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_song(self, request, pk=None):
        """Thêm bài hát vào playlist"""
        playlist = self.get_object()
        
        # Kiểm tra quyền chỉnh sửa playlist
        if playlist.user != request.user:
            return Response(
                {'error': 'Bạn không có quyền chỉnh sửa playlist này'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        song_id = request.data.get('song_id')
        if not song_id:
            return Response(
                {'error': 'Cần cung cấp ID bài hát'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Kiểm tra số lượng bài hát trong playlist
        song_count = playlist.songs.count()
        if song_count >= 1000:  # Giới hạn tối đa 1000 bài/playlist
            return Response(
                {'error': 'Playlist đã đạt giới hạn tối đa 1000 bài hát'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            song = Song.objects.get(id=song_id)
            
            # Kiểm tra bài hát đã có trong playlist chưa
            if playlist.songs.filter(id=song_id).exists():
                return Response(
                    {'error': 'Bài hát đã có trong playlist'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Kiểm tra file audio hợp lệ
            if not song.audio_file:
                return Response(
                    {'error': 'Bài hát không có file audio'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            playlist.songs.add(song)
            return Response({'status': 'Đã thêm bài hát vào playlist'})
        except Song.DoesNotExist:
            return Response(
                {'error': 'Không tìm thấy bài hát'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def remove_song(self, request, pk=None):
        """Xóa bài hát khỏi playlist"""
        playlist = self.get_object()
        
        # Kiểm tra quyền chỉnh sửa playlist
        if playlist.user != request.user:
            return Response(
                {'error': 'Bạn không có quyền chỉnh sửa playlist này'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        song_id = request.data.get('song_id')
        if not song_id:
            return Response(
                {'error': 'Cần cung cấp ID bài hát'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            song = Song.objects.get(id=song_id)
            
            # Kiểm tra bài hát có trong playlist không
            if not playlist.songs.filter(id=song_id).exists():
                return Response(
                    {'error': 'Bài hát không có trong playlist'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            playlist.songs.remove(song)
            return Response({'status': 'Đã xóa bài hát khỏi playlist'})
        except Song.DoesNotExist:
            return Response(
                {'error': 'Không tìm thấy bài hát'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_cover_image(self, request, pk=None):
        """Cập nhật ảnh bìa cho playlist"""
        playlist = self.get_object()
        
        # Kiểm tra quyền chỉnh sửa playlist
        if playlist.user != request.user:
            return Response(
                {'error': 'Bạn không có quyền chỉnh sửa playlist này'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Lấy ảnh từ request
        image_file = request.FILES.get('cover_image')
        if not image_file:
            # Thử lấy ảnh bìa từ bài hát trong playlist
            song_id = request.data.get('song_id')
            if song_id:
                try:
                    song = Song.objects.get(id=song_id)
                    if song.cover_image:
                        playlist.cover_image = song.cover_image
                        playlist.save()
                        return Response({'status': 'Đã cập nhật ảnh bìa từ bài hát'})
                    else:
                        return Response(
                            {'error': 'Bài hát không có ảnh bìa'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Song.DoesNotExist:
                    return Response(
                        {'error': 'Không tìm thấy bài hát'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {'error': 'Cần cung cấp file ảnh hoặc ID bài hát'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Kiểm tra kích thước ảnh (tối đa 5MB)
        if image_file.size > 5 * 1024 * 1024:
            return Response(
                {'error': 'Kích thước ảnh không được vượt quá 5MB'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Kiểm tra định dạng file
        valid_types = ['image/jpeg', 'image/png', 'image/jpg']
        if image_file.content_type not in valid_types:
            return Response(
                {'error': 'Định dạng ảnh không hợp lệ. Chỉ chấp nhận JPEG, JPG và PNG'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Cập nhật ảnh bìa
        playlist.cover_image = image_file
        playlist.save()
        
        return Response({'status': 'Đã cập nhật ảnh bìa thành công'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_privacy(self, request, pk=None):
        """Chuyển đổi trạng thái công khai/riêng tư của playlist"""
        playlist = self.get_object()
        
        # Kiểm tra quyền chỉnh sửa playlist
        if playlist.user != request.user:
            return Response(
                {'error': 'Bạn không có quyền chỉnh sửa playlist này'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Đổi trạng thái
        playlist.is_public = not playlist.is_public
        playlist.save()
        
        status_text = 'công khai' if playlist.is_public else 'riêng tư'
        return Response({'status': f'Đã chuyển playlist sang chế độ {status_text}'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        """Theo dõi playlist"""
        playlist = self.get_object()
        user = request.user
        
        # Kiểm tra quyền xem playlist
        if not playlist.is_public and playlist.user != user:
            return Response(
                {'error': 'Bạn không có quyền xem playlist riêng tư này'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Kiểm tra đã theo dõi chưa
        if playlist.followers.filter(id=user.id).exists():
            return Response(
                {'error': 'Bạn đã theo dõi playlist này rồi'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        playlist.followers.add(user)
        return Response({'status': 'Đã theo dõi playlist thành công'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk=None):
        """Bỏ theo dõi playlist"""
        playlist = self.get_object()
        user = request.user
        
        # Kiểm tra đang theo dõi không
        if not playlist.followers.filter(id=user.id).exists():
            return Response(
                {'error': 'Bạn chưa theo dõi playlist này'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        playlist.followers.remove(user)
        return Response({'status': 'Đã bỏ theo dõi playlist thành công'})
        
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def followers(self, request, pk=None):
        """Lấy danh sách người theo dõi playlist"""
        playlist = self.get_object()
        
        # Kiểm tra quyền xem danh sách người theo dõi
        if not playlist.is_public and playlist.user != request.user:
            return Response(
                {'error': 'Bạn không có quyền xem thông tin playlist riêng tư này'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        followers = playlist.followers.all()
        serializer = UserBasicSerializer(followers, many=True)
        return Response({
            'playlist_id': playlist.id,
            'playlist_name': playlist.name,
            'followers_count': followers.count(),
            'followers': serializer.data
        })

class AlbumViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Album"""
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    
    def get_permissions(self):
        """
        Cho phép người dùng chưa đăng nhập xem thông tin album,
        nhưng chỉ người dùng đã đăng nhập mới có thể thao tác.
        """
        if self.action in ['list', 'retrieve', 'songs', 'related']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AlbumDetailSerializer
        return AlbumSerializer
    
    def get_serializer(self, *args, **kwargs):
        """Đảm bảo request context được truyền vào serializer"""
        kwargs['context'] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)
    
    def get_serializer_context(self):
        """Thêm request vào context của serializer"""
        context = super().get_serializer_context()
        return context
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def songs(self, request, pk=None):
        """Lấy danh sách bài hát trong album"""
        album = self.get_object()
        songs = Song.objects.filter(album=album.title)
        serializer = SongSerializer(songs, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def related(self, request, pk=None):
        """Lấy danh sách album liên quan"""
        album = self.get_object()
        # Lấy album cùng nghệ sĩ
        related_albums = Album.objects.filter(artist=album.artist).exclude(id=album.id)[:5]
        serializer = AlbumSerializer(related_albums, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def new(self, request):
        """Lấy album mới phát hành"""
        three_months_ago = datetime.now().date() - timedelta(days=90)
        new_albums = Album.objects.filter(release_date__gte=three_months_ago).order_by('-release_date')[:10]
        serializer = self.get_serializer(new_albums, many=True)
        return Response(serializer.data)

class GenreViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Genre"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    
    def get_permissions(self):
        """
        Cho phép người dùng chưa đăng nhập xem thông tin thể loại,
        nhưng chỉ người dùng đã đăng nhập mới có thể thao tác.
        """
        if self.action in ['list', 'retrieve', 'songs', 'artists']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GenreDetailSerializer
        return GenreSerializer
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def songs(self, request, pk=None):
        """Lấy danh sách bài hát thuộc thể loại"""
        genre = self.get_object()
        songs = Song.objects.filter(genre=genre.name)
        
        # Phân trang
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = SongSerializer(songs[start:end], many=True)
        
        return Response({
            'total': songs.count(),
            'page': page, 
            'page_size': page_size,
            'songs': serializer.data
        })
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def artists(self, request, pk=None):
        """Lấy danh sách nghệ sĩ nổi bật trong thể loại"""
        genre = self.get_object()
        
        # Lấy nghệ sĩ nổi bật trong thể loại này
        artists = {}
        for song in Song.objects.filter(genre=genre.name):
            if song.artist in artists:
                artists[song.artist] += 1
            else:
                artists[song.artist] = 1
        
        # Sắp xếp theo số lượng bài hát
        top_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return Response([
            {'name': artist[0], 'songs_count': artist[1]} 
            for artist in top_artists
        ])
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def top_songs(self, request, pk=None):
        """Lấy danh sách bài hát nổi bật theo thể loại"""
        genre = self.get_object()
        top_songs = Song.objects.filter(genre=genre.name).order_by('-play_count')[:10]
        serializer = SongSerializer(top_songs, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet để xử lý các thao tác CRUD với Comment"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def get_permissions(self):
        """
        Cho phép người dùng chưa đăng nhập xem bình luận,
        nhưng chỉ người dùng đã đăng nhập mới có thể thêm, sửa, xóa bình luận.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
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
        """Lấy thư viện nhạc của người dùng, bao gồm playlist, bài hát yêu thích và gần đây đã nghe"""
        # Lấy playlist của người dùng
        playlists = Playlist.objects.filter(user=request.user)
        playlist_serializer = PlaylistSerializer(playlists, many=True)
        
        # Lấy bài hát yêu thích
        user = request.user
        favorites = user.favorite_songs.all()
        favorites_serializer = SongSerializer(favorites, many=True)
        
        # Lấy lịch sử nghe nhạc gần đây
        history = SongPlayHistory.objects.filter(
            user=request.user
        ).order_by('-played_at').select_related('song')[:10]
        
        recent_songs = []
        seen_song_ids = set()
        
        for item in history:
            if item.song.id not in seen_song_ids:
                recent_songs.append(item.song)
                seen_song_ids.add(item.song.id)
        
        recent_serializer = SongSerializer(recent_songs, many=True)
        
        # Lấy số lượng bài hát đã tải xuống
        offline_count = OfflineDownload.objects.filter(
            user=request.user, 
            status='COMPLETED',
            is_active=True
        ).count()
        
        # Lấy không gian đĩa đã sử dụng cho tải xuống offline (đơn vị MB)
        offline_space = OfflineDownload.objects.filter(
            user=request.user, 
            status='COMPLETED',
            is_active=True
        ).count() * 5  # Ước tính mỗi bài hát ~5MB
        
        return Response({
            'playlists': playlist_serializer.data,
            'favorites': favorites_serializer.data,
            'recent': recent_serializer.data,
            'offline': {
                'count': offline_count,
                'space_used_mb': offline_space,
                'url': reverse('offline-downloads')
            }
        })

class TrendingSongsView(APIView):
    """Lấy bài hát xu hướng"""
    permission_classes = [AllowAny]
    
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
    permission_classes = [AllowAny]
    
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
        
        # Lưu lịch sử tìm kiếm chỉ khi đã đăng nhập
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

class NewAlbumsView(APIView):
    """Lấy danh sách album mới phát hành"""
    permission_classes = [AllowAny]
    
    def get(self, request, format=None):
        # Lấy album phát hành trong 3 tháng gần nhất
        three_months_ago = datetime.now().date() - timedelta(days=90)
        new_albums = Album.objects.filter(release_date__gte=three_months_ago).order_by('-release_date')
        
        # Phân trang
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = AlbumSerializer(new_albums[start:end], many=True)
        
        return Response({
            'total': new_albums.count(),
            'page': page, 
            'page_size': page_size,
            'albums': serializer.data
        })

class FeaturedPlaylistsView(APIView):
    """Lấy danh sách playlist được yêu thích nhất"""
    permission_classes = [AllowAny]
    
    def get(self, request, format=None):
        # Lấy playlist công khai được nhiều người follow nhất
        popular_playlists = Playlist.objects.filter(is_public=True).annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')
        
        # Phân trang
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = PlaylistSerializer(popular_playlists[start:end], many=True)
        
        return Response({
            'total': popular_playlists.count(),
            'page': page, 
            'page_size': page_size,
            'playlists': serializer.data
        })

class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet chỉ đọc cho nghệ sĩ"""
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def songs(self, request, pk=None):
        """Lấy danh sách bài hát của nghệ sĩ"""
        artist = self.get_object()
        songs = Song.objects.filter(artist=artist.name)
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        """Lấy danh sách album của nghệ sĩ"""
        artist = self.get_object()
        albums = Album.objects.filter(artist=artist.name)
        serializer = AlbumSerializer(albums, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def popular(self, request):
        """Lấy danh sách nghệ sĩ phổ biến dựa trên số lượng bài hát và số lượt nghe"""
        # Lấy số lượng bài hát theo nghệ sĩ
        artists = Artist.objects.all()
        
        # Dictionary để lưu số lượng bài hát và lượt nghe cho mỗi nghệ sĩ
        artists_data = []
        
        for artist in artists:
            songs = Song.objects.filter(artist=artist.name)
            song_count = songs.count()
            play_count = songs.aggregate(total_plays=Sum('play_count'))['total_plays'] or 0
            
            artist_info = {
                'artist': artist,
                'song_count': song_count,
                'play_count': play_count
            }
            artists_data.append(artist_info)
        
        # Sắp xếp theo số lượt nghe (nếu bằng nhau thì sắp theo số bài hát)
        sorted_artists = sorted(
            artists_data, 
            key=lambda x: (x['play_count'], x['song_count']), 
            reverse=True
        )
        
        # Giới hạn số lượng trả về
        limit = int(request.query_params.get('limit', 10))
        popular_artists = sorted_artists[:limit]
        
        # Trả về dữ liệu với thông tin bổ sung
        result = []
        for artist_info in popular_artists:
            # Tạo dữ liệu artist dưới dạng dict
            artist_data = ArtistSerializer(artist_info['artist']).data
            # Chuyển OrderedDict hoặc đối tượng khác thành dict tiêu chuẩn
            artist_data = dict(artist_data)
            # Thêm thông tin bổ sung vào dict
            artist_data['song_count'] = artist_info['song_count']
            artist_data['play_count'] = artist_info['play_count']
            result.append(artist_data)
            
        return Response(result)

# Cho phép người dùng chưa đăng nhập xem trang chơi nhạc 
def play_song(request):
    """Phương thức cho phép hiển thị trang chơi nhạc cho cả người dùng đã đăng nhập và chưa đăng nhập"""
    # Đường dẫn file mp3 mẫu, có thể lấy từ database sau
    song_url = '/media/songs/2025/04/28/TinhNho-ThanhHien-5825173_XH1ISay.mp3'
    return render(request, 'play_song.html', {'song_url': song_url})

# Thêm các API cho Queue
class QueueView(APIView):
    """Xem hàng đợi phát nhạc hiện tại"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        # Lấy hoặc tạo queue cho user
        queue, created = Queue.objects.get_or_create(user=request.user)
        serializer = QueueSerializer(queue)
        return Response(serializer.data)

class AddToQueueView(APIView):
    """Thêm bài hát vào hàng đợi phát"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        song_id = request.data.get('song_id')
        if not song_id:
            return Response({'error': 'Cần cung cấp ID bài hát'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Kiểm tra bài hát tồn tại
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            return Response({'error': 'Bài hát không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
        
        # Lấy hoặc tạo queue cho user
        queue, created = Queue.objects.get_or_create(user=request.user)
        
        # Vị trí cuối cùng trong queue
        last_position = QueueItem.objects.filter(queue=queue).order_by('-position').first()
        position = 1 if not last_position else last_position.position + 1
        
        # Tạo queue item mới
        queue_item = QueueItem.objects.create(
            queue=queue,
            song=song,
            position=position
        )
        
        return Response({'status': 'Đã thêm vào hàng đợi', 'position': position})

class RemoveFromQueueView(APIView):
    """Xóa bài hát khỏi hàng đợi phát"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, position, format=None):
        # Lấy queue của user
        try:
            queue = Queue.objects.get(user=request.user)
        except Queue.DoesNotExist:
            return Response({'error': 'Queue không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
        
        # Xóa bài hát ở vị trí chỉ định
        try:
            queue_item = QueueItem.objects.get(queue=queue, position=position)
            queue_item.delete()
            
            # Cập nhật lại vị trí các bài hát trong queue
            items = QueueItem.objects.filter(queue=queue, position__gt=position).order_by('position')
            for item in items:
                item.position -= 1
                item.save()
            
            return Response({'status': 'Đã xóa khỏi hàng đợi'})
        except QueueItem.DoesNotExist:
            return Response({'error': 'Không tìm thấy bài hát ở vị trí này'}, status=status.HTTP_404_NOT_FOUND)

class ClearQueueView(APIView):
    """Xóa toàn bộ hàng đợi phát"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, format=None):
        # Lấy queue của user
        try:
            queue = Queue.objects.get(user=request.user)
            QueueItem.objects.filter(queue=queue).delete()
            return Response({'status': 'Đã xóa toàn bộ hàng đợi'})
        except Queue.DoesNotExist:
            return Response({'error': 'Queue không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

# Thêm API cho User Status
class UserStatusView(APIView):
    """Xem và cập nhật trạng thái nghe nhạc"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        # Lấy hoặc tạo status cho user
        status_obj, created = UserStatus.objects.get_or_create(user=request.user)
        serializer = UserStatusSerializer(status_obj)
        return Response(serializer.data)
    
    def put(self, request, format=None):
        # Cập nhật status cho user
        status_obj, created = UserStatus.objects.get_or_create(user=request.user)
        
        data = {}
        if 'currently_playing' in request.data:
            try:
                song = Song.objects.get(id=request.data['currently_playing'])
                data['currently_playing'] = song
            except Song.DoesNotExist:
                pass
        
        if 'status_text' in request.data:
            data['status_text'] = request.data['status_text']
        
        if 'is_listening' in request.data:
            data['is_listening'] = request.data['is_listening']
        
        for key, value in data.items():
            setattr(status_obj, key, value)
        
        status_obj.save()
        serializer = UserStatusSerializer(status_obj)
        return Response(serializer.data)

# Thêm API cho Messaging và Sharing
class MessageListView(APIView):
    """Xem tin nhắn"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        # Lấy tin nhắn đã nhận
        received = Message.objects.filter(receiver=request.user).order_by('-timestamp')
        # Lấy tin nhắn đã gửi
        sent = Message.objects.filter(sender=request.user).order_by('-timestamp')
        
        # Đánh dấu tin nhắn đã đọc
        for msg in received.filter(is_read=False):
            msg.is_read = True
            msg.save()
        
        received_serializer = MessageSerializer(received, many=True)
        sent_serializer = MessageSerializer(sent, many=True)
        
        return Response({
            'received': received_serializer.data,
            'sent': sent_serializer.data
        })

class SendMessageView(APIView):
    """Gửi tin nhắn"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        receiver_id = request.data.get('receiver_id')
        content = request.data.get('content')
        
        if not receiver_id or not content:
            return Response({
                'error': 'Cần cung cấp ID người nhận và nội dung tin nhắn'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({'error': 'Người nhận không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
        
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content,
            message_type='TEXT'
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ShareSongView(APIView):
    """Chia sẻ bài hát với bạn bè"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, song_id, format=None):
        receiver_id = request.data.get('receiver_id')
        content = request.data.get('content', '')
        
        if not receiver_id:
            return Response({
                'error': 'Cần cung cấp ID người nhận'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            receiver = User.objects.get(id=receiver_id)
            song = Song.objects.get(id=song_id)
        except User.DoesNotExist:
            return Response({'error': 'Người nhận không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
        except Song.DoesNotExist:
            return Response({'error': 'Bài hát không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
        
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content,
            message_type='SONG',
            shared_song=song
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SharePlaylistView(APIView):
    """Chia sẻ playlist với bạn bè"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, playlist_id, format=None):
        receiver_id = request.data.get('receiver_id')
        content = request.data.get('content', '')
        
        if not receiver_id:
            return Response({
                'error': 'Cần cung cấp ID người nhận'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            receiver = User.objects.get(id=receiver_id)
            playlist = Playlist.objects.get(id=playlist_id)
        except User.DoesNotExist:
            return Response({'error': 'Người nhận không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
        except Playlist.DoesNotExist:
            return Response({'error': 'Playlist không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
        
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content,
            message_type='PLAYLIST',
            shared_playlist=playlist
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# Thêm API cho thống kê và xu hướng cá nhân
class UserStatisticsView(APIView):
    """Thống kê thời gian nghe theo thể loại"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Lấy tổng số bài hát đã nghe
        total_plays = SongPlayHistory.objects.filter(user=user).count()
        
        # Thống kê theo thể loại
        genre_stats = {}
        for play in SongPlayHistory.objects.filter(user=user).select_related('song'):
            genre = play.song.genre
            if genre in genre_stats:
                genre_stats[genre] += 1
            else:
                genre_stats[genre] = 1
        
        # Sắp xếp theo số lượt nghe
        sorted_genres = sorted(genre_stats.items(), key=lambda x: x[1], reverse=True)
        
        # Tỷ lệ phần trăm theo thể loại
        genre_percentages = []
        for genre, count in sorted_genres:
            percentage = (count / total_plays) * 100 if total_plays > 0 else 0
            genre_percentages.append({
                'genre': genre,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Thời gian nghe trung bình mỗi ngày
        return Response({
            'total_plays': total_plays,
            'genre_stats': genre_percentages,
        })

class PersonalTrendsView(APIView):
    """Xu hướng nghe nhạc cá nhân"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Bài hát nghe gần đây nhất
        recent_history = SongPlayHistory.objects.filter(user=user).order_by('-played_at')[:30]
        
        # Chỉ hiển thị bài hát không trùng lặp
        recent_plays = []
        song_ids = set()
        
        for history in recent_history:
            if history.song.pk not in song_ids:
                recent_plays.append(history)
                song_ids.add(history.song.pk)
                if len(recent_plays) >= 10:  # Giới hạn ở 10 bài khác nhau
                    break
        
        recent_serializer = SongPlayHistorySerializer(recent_plays, many=True, context={'request': request})
        
        # Thể loại nghe nhiều nhất trong 30 ngày qua
        last_month = datetime.now() - timedelta(days=30)
        genre_count = {}
        
        for play in SongPlayHistory.objects.filter(user=user, played_at__gte=last_month).select_related('song'):
            genre = play.song.genre
            if genre in genre_count:
                genre_count[genre] += 1
            else:
                genre_count[genre] = 1
        
        top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Sắp xếp top_genres thành danh sách dict
        top_genres_list = [{'genre': genre, 'count': count} for genre, count in top_genres]
        
        return Response({
            'recent_plays': recent_serializer.data,
            'top_genres': top_genres_list
        })

# Thêm API cho đề xuất cá nhân hóa
class RecommendationsView(APIView):
    """Đề xuất bài hát dựa trên lịch sử nghe"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Lấy 5 thể loại nghe nhiều nhất
        genre_count = {}
        for play in SongPlayHistory.objects.filter(user=user).select_related('song'):
            genre = play.song.genre
            if genre in genre_count:
                genre_count[genre] += 1
            else:
                genre_count[genre] = 1
        
        top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:5]
        top_genres = [genre for genre, _ in top_genres]
        
        # Lấy bài hát đã nghe
        played_songs = SongPlayHistory.objects.filter(user=user).values_list('song_id', flat=True)
        
        # Đề xuất bài hát từ thể loại yêu thích mà chưa nghe
        recommendations = Song.objects.filter(genre__in=top_genres).exclude(id__in=played_songs).order_by('-play_count')[:20]
        
        serializer = SongSerializer(recommendations, many=True)
        return Response(serializer.data)

class LikedBasedRecommendationsView(APIView):
    """Đề xuất bài hát dựa trên bài hát đã thích"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Lấy thể loại từ bài hát đã thích
        liked_songs = user.favorite_songs.all()
        if not liked_songs.exists():
            return Response([])
        
        genre_count = {}
        for song in liked_songs:
            genre = song.genre
            if genre in genre_count:
                genre_count[genre] += 1
            else:
                genre_count[genre] = 1
        
        top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:3]
        top_genres = [genre for genre, _ in top_genres]
        
        # Lấy bài hát từ thể loại tương tự nhưng chưa thích
        liked_ids = liked_songs.values_list('id', flat=True)
        recommendations = Song.objects.filter(genre__in=top_genres).exclude(id__in=liked_ids).order_by('-likes_count')[:15]
        
        serializer = SongSerializer(recommendations, many=True)
        return Response(serializer.data)

class YouMayLikeView(APIView):
    """Gợi ý 'Có thể bạn sẽ thích'"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Lấy tất cả bài hát đã nghe
        played_ids = SongPlayHistory.objects.filter(user=user).values_list('song_id', flat=True)
        
        # Lấy tất cả bài hát đã thích
        liked_ids = user.favorite_songs.values_list('id', flat=True)
        
        # Loại bỏ những bài đã nghe hoặc đã thích
        excluded_ids = list(played_ids) + list(liked_ids)
        
        # Lấy bài hát phổ biến mà user chưa nghe
        popular_songs = Song.objects.exclude(id__in=excluded_ids).order_by('-play_count', '-likes_count')[:10]
        
        serializer = SongSerializer(popular_songs, many=True)
        return Response(serializer.data)

# Thêm API cho lịch sử
class PlayHistoryView(APIView):
    """Xem lịch sử nghe nhạc"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Lấy lịch sử phát
        history = SongPlayHistory.objects.filter(user=user).order_by('-played_at')
        
        # Phân trang
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        # Lấy lịch sử phát
        history_records = history[start:end]
        
        # Lấy bài hát không trùng lặp nếu có tham số unique=true
        unique = request.query_params.get('unique', 'false').lower() == 'true'
        
        if unique:
            unique_songs = []
            song_ids = set()
            
            for record in history_records:
                if record.song.pk not in song_ids:
                    unique_songs.append(record)
                    song_ids.add(record.song.pk)
            
            # Sử dụng SongPlayHistorySerializer với data là unique_songs
            serializer = SongPlayHistorySerializer(unique_songs, many=True, context={'request': request})
        else:
            # Sử dụng SongPlayHistorySerializer với data là history_records
            serializer = SongPlayHistorySerializer(history_records, many=True, context={'request': request})
        
        return Response({
            'total': history.count(),
            'page': page, 
            'page_size': page_size,
            'history': serializer.data
        })

class SearchHistoryView(APIView):
    """Xem lịch sử tìm kiếm"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        
        # Lấy lịch sử tìm kiếm
        history = SearchHistory.objects.filter(user=user).order_by('-timestamp')
        
        # Phân trang
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = SearchHistorySerializer(history[start:end], many=True)
        
        return Response({
            'total': history.count(),
            'page': page, 
            'page_size': page_size,
            'history': serializer.data
        })
    
    def delete(self, request, format=None):
        """Xóa lịch sử tìm kiếm"""
        user = request.user
        SearchHistory.objects.filter(user=user).delete()
        return Response({'status': 'Đã xóa lịch sử tìm kiếm'}, status=status.HTTP_204_NO_CONTENT)

class SongRecommendationView(APIView):
    """
    API endpoint trả về danh sách bài hát được gợi ý cho người dùng
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from .models import UserRecommendation
            from .serializers import SongSerializer
            from .utils import generate_song_recommendations
            
            # Lấy số lượng từ query params, mặc định là 10
            limit = request.query_params.get('limit', 10)
            try:
                limit = int(limit)
                # Giới hạn số lượng tối đa là 50
                limit = min(limit, 50)
            except (ValueError, TypeError):
                limit = 10
                
            # Lấy đề xuất từ cơ sở dữ liệu
            user_recommendations = UserRecommendation.objects.filter(user=request.user).order_by('-score')[:limit]
            recommended_songs = [rec.song for rec in user_recommendations]
            
            # Nếu không có đề xuất trong cơ sở dữ liệu, tạo mới
            if not recommended_songs:
                # Tự động tạo đề xuất nếu không có sẵn
                recommended_songs = generate_song_recommendations(request.user, limit=limit)
                
                # Lưu các đề xuất mới vào cơ sở dữ liệu
                if recommended_songs:
                    for i, song in enumerate(recommended_songs):
                        score = 1.0 - (i / len(recommended_songs))
                        UserRecommendation.objects.create(
                            user=request.user,
                            song=song,
                            score=score
                        )
            
            # Serialize kết quả
            serializer = SongSerializer(recommended_songs, many=True, context={'request': request})
            
            return Response({
                'results': serializer.data,
                'count': len(recommended_songs)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# API cho Admin quản lý Collaborative Playlist
class AdminCollaborativePlaylistListView(generics.ListAPIView):
    """API để admin xem tất cả các collaborative playlist"""
    permission_classes = [IsAdminUser]
    serializer_class = PlaylistDetailSerializer
    queryset = Playlist.objects.filter(is_collaborative=True)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'user__username']
    ordering_fields = ['name', 'created_at', 'updated_at']
    
    def get_queryset(self):
        queryset = Playlist.objects.filter(is_collaborative=True).order_by('-updated_at')
        
        # Lọc theo chủ sở hữu
        owner_id = self.request.query_params.get('owner_id')
        if owner_id:
            queryset = queryset.filter(user_id=owner_id)
            
        # Lọc theo người cộng tác
        collaborator_id = self.request.query_params.get('collaborator_id')
        if collaborator_id:
            queryset = queryset.filter(collaborators__id=collaborator_id)
            
        # Lọc theo khoảng thời gian tạo
        created_after = self.request.query_params.get('created_after')
        created_before = self.request.query_params.get('created_before')
        if created_after and created_before:
            queryset = queryset.filter(created_at__range=[created_after, created_before])
            
        return queryset

class AdminCollaborativePlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API để admin xem chi tiết và chỉnh sửa một collaborative playlist"""
    permission_classes = [IsAdminUser]
    serializer_class = PlaylistDetailSerializer
    queryset = Playlist.objects.filter(is_collaborative=True)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Lưu lại thông tin cũ để ghi vào lịch sử
        old_data = {
            'name': instance.name,
            'description': instance.description,
            'is_public': instance.is_public
        }
        
        self.perform_update(serializer)
        
        # Ghi nhật ký hành động
        new_data = {
            'name': instance.name,
            'description': instance.description,
            'is_public': instance.is_public
        }
        
        # Chỉ ghi nhật ký nếu có thay đổi
        if old_data != new_data:
            details = {
                'old': old_data,
                'new': new_data,
                'admin_action': True
            }
            
            PlaylistEditHistory.log_action(
                playlist=instance,
                user=request.user,
                action='UPDATE_INFO',
                details=details
            )
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Ghi log trước khi xóa
        PlaylistEditHistory.log_action(
            playlist=instance,
            user=request.user,
            action='DELETE',
            details={'admin_action': True}
        )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class AdminPlaylistCollaboratorsView(generics.ListAPIView):
    """API để admin xem danh sách người cộng tác của một playlist"""
    permission_classes = [IsAdminUser]
    serializer_class = CollaboratorRoleSerializer
    
    def get_queryset(self):
        playlist_id = self.kwargs.get('playlist_id')
        return CollaboratorRole.objects.filter(playlist_id=playlist_id)

class AdminAddCollaboratorView(generics.CreateAPIView):
    """API để admin thêm người cộng tác vào playlist"""
    permission_classes = [IsAdminUser]
    serializer_class = CollaboratorRoleCreateSerializer
    
    def perform_create(self, serializer):
        collaborator_role = serializer.save(added_by=self.request.user)
        
        # Ghi nhật ký hành động
        PlaylistEditHistory.log_action(
            playlist=collaborator_role.playlist,
            user=self.request.user,
            action='ADD_COLLABORATOR',
            details={
                'role': collaborator_role.role,
                'admin_action': True
            },
            related_user=collaborator_role.user
        )

class AdminRemoveCollaboratorView(APIView):
    """API để admin xóa người cộng tác khỏi playlist"""
    permission_classes = [IsAdminUser]
    
    def delete(self, request, playlist_id, user_id):
        try:
            playlist = Playlist.objects.get(id=playlist_id, is_collaborative=True)
            user = User.objects.get(id=user_id)
            
            # Kiểm tra xem người dùng có phải là chủ sở hữu không
            if user == playlist.user:
                return Response(
                    {"error": "Không thể xóa chủ sở hữu playlist khỏi danh sách cộng tác viên"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Kiểm tra xem người dùng có phải là cộng tác viên không
            try:
                role = CollaboratorRole.objects.get(playlist=playlist, user=user)
                role.delete()
                
                # Ghi nhật ký hành động
                PlaylistEditHistory.log_action(
                    playlist=playlist,
                    user=request.user,
                    action='REMOVE_COLLABORATOR',
                    details={'admin_action': True},
                    related_user=user
                )
                
                return Response(status=status.HTTP_204_NO_CONTENT)
            except CollaboratorRole.DoesNotExist:
                return Response(
                    {"error": "Người dùng không phải là cộng tác viên của playlist này"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Playlist.DoesNotExist:
            return Response(
                {"error": "Không tìm thấy playlist collaborative"},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Không tìm thấy người dùng"},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminChangeCollaboratorRoleView(APIView):
    """API để admin thay đổi vai trò của người cộng tác"""
    permission_classes = [IsAdminUser]
    
    def post(self, request, playlist_id, user_id):
        try:
            playlist = Playlist.objects.get(id=playlist_id, is_collaborative=True)
            user = User.objects.get(id=user_id)
            
            # Kiểm tra xem người dùng có phải là chủ sở hữu không
            if user == playlist.user:
                return Response(
                    {"error": "Không thể thay đổi vai trò của chủ sở hữu playlist"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Kiểm tra xem người dùng có phải là cộng tác viên không
            try:
                role = CollaboratorRole.objects.get(playlist=playlist, user=user)
                
                # Lấy vai trò mới từ request
                new_role = request.data.get('role')
                if not new_role or new_role not in [choice[0] for choice in CollaboratorRole.ROLE_CHOICES]:
                    return Response(
                        {"error": f"Vai trò không hợp lệ. Các vai trò hợp lệ: {[choice[0] for choice in CollaboratorRole.ROLE_CHOICES]}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                old_role = role.role
                role.role = new_role
                role.save()
                
                # Ghi nhật ký hành động
                PlaylistEditHistory.log_action(
                    playlist=playlist,
                    user=request.user,
                    action='CHANGE_ROLE',
                    details={
                        'old_role': old_role,
                        'new_role': new_role,
                        'admin_action': True
                    },
                    related_user=user
                )
                
                return Response(CollaboratorRoleSerializer(role).data)
            except CollaboratorRole.DoesNotExist:
                return Response(
                    {"error": "Người dùng không phải là cộng tác viên của playlist này"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Playlist.DoesNotExist:
            return Response(
                {"error": "Không tìm thấy playlist collaborative"},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Không tìm thấy người dùng"},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminPlaylistEditHistoryView(generics.ListAPIView):
    """API để admin xem lịch sử chỉnh sửa của một playlist"""
    permission_classes = [IsAdminUser]
    serializer_class = PlaylistEditHistorySerializer
    
    def get_queryset(self):
        playlist_id = self.kwargs.get('playlist_id')
        return PlaylistEditHistory.objects.filter(playlist_id=playlist_id).order_by('-timestamp')
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context

class AdminRestorePlaylistView(APIView):
    """API để admin khôi phục playlist về một phiên bản trước đó"""
    permission_classes = [IsAdminUser]
    
    def post(self, request, playlist_id):
        # Lấy ID của bản ghi lịch sử cần khôi phục
        history_id = request.data.get('history_id')
        if not history_id:
            return Response(
                {"error": "Cần cung cấp ID của bản ghi lịch sử để khôi phục"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            playlist = Playlist.objects.get(id=playlist_id, is_collaborative=True)
            history_entry = PlaylistEditHistory.objects.get(id=history_id, playlist=playlist)
            
            # Xử lý khôi phục dựa trên loại hành động
            if history_entry.action == 'UPDATE_INFO':
                # Khôi phục thông tin từ bản ghi lịch sử
                old_data = history_entry.details.get('old', {})
                if old_data:
                    for key, value in old_data.items():
                        if hasattr(playlist, key):
                            setattr(playlist, key, value)
                    playlist.save()
                    
                    # Ghi nhật ký hành động khôi phục
                    PlaylistEditHistory.log_action(
                        playlist=playlist,
                        user=request.user,
                        action='RESTORE',
                        details={
                            'restored_from': history_id,
                            'admin_action': True
                        }
                    )
                    
                    return Response({"status": "Đã khôi phục thông tin playlist thành công"})
            elif history_entry.action in ['ADD_SONG', 'REMOVE_SONG']:
                # Khôi phục bài hát nếu có
                if history_entry.related_song:
                    if history_entry.action == 'ADD_SONG':
                        # Nếu trước đó là thêm bài hát, giờ ta xóa nó
                        playlist.songs.remove(history_entry.related_song)
                    else:
                        # Nếu trước đó là xóa bài hát, giờ ta thêm lại
                        playlist.songs.add(history_entry.related_song)
                        
                    PlaylistEditHistory.log_action(
                        playlist=playlist,
                        user=request.user,
                        action='RESTORE',
                        details={
                            'restored_from': history_id,
                            'admin_action': True
                        },
                        related_song=history_entry.related_song
                    )
                    
                    return Response({"status": "Đã khôi phục bài hát thành công"})
            
            # Các trường hợp không hỗ trợ khôi phục
            return Response(
                {"error": f"Không hỗ trợ khôi phục cho hành động {history_entry.get_action_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Playlist.DoesNotExist:
            return Response(
                {"error": "Không tìm thấy playlist collaborative"},
                status=status.HTTP_404_NOT_FOUND
            )
        except PlaylistEditHistory.DoesNotExist:
            return Response(
                {"error": "Không tìm thấy bản ghi lịch sử"},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminTopSongsReportView(APIView):
    """API hiển thị báo cáo chi tiết về top bài hát cho admin"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, format=None):
        # Lấy tham số từ request
        period = request.query_params.get('period', 'month')  # Mặc định là thống kê theo tháng
        limit = int(request.query_params.get('limit', 20))    # Số lượng bài hát hiển thị
        
        # Xác định khoảng thời gian dựa trên period
        now = django.utils.timezone.now()
        if period == 'week':
            start_date = now - timedelta(days=7)
            period_label = '7 ngày qua'
        elif period == 'month':
            start_date = now - timedelta(days=30)
            period_label = '30 ngày qua'
        elif period == 'year':
            start_date = now - timedelta(days=365)
            period_label = '365 ngày qua'
        else:  # Mặc định là all
            start_date = None
            period_label = 'Tất cả thời gian'
        
        # Query bài hát
        if start_date:
            # Lấy số lượng play trong khoảng thời gian
            recent_plays = SongPlayHistory.objects.filter(
                played_at__gte=start_date
            ).values('song').annotate(
                recent_play_count=Count('id')
            ).order_by('-recent_play_count')[:limit]
            
            # Lấy thông tin bài hát
            song_ids = [item['song'] for item in recent_plays]
            songs = Song.objects.filter(id__in=song_ids)
            
            # Kết hợp dữ liệu
            results = []
            for song in songs:
                play_item = next((item for item in recent_plays if item['song'] == song.id), None)
                if play_item:
                    results.append({
                        'id': song.id,
                        'title': song.title,
                        'artist': song.artist,
                        'album': song.album,
                        'total_plays': song.play_count,
                        'recent_plays': play_item['recent_play_count'],
                        'likes': song.likes_count,
                    })
            
            # Sắp xếp lại theo số lượt nghe gần đây
            results = sorted(results, key=lambda x: x['recent_plays'], reverse=True)
            
        else:
            # Lấy bài hát có lượt play cao nhất mọi thời gian
            top_songs = Song.objects.all().order_by('-play_count')[:limit]
            results = []
            for song in top_songs:
                results.append({
                    'id': song.id,
                    'title': song.title,
                    'artist': song.artist,
                    'album': song.album,
                    'total_plays': song.play_count,
                    'recent_plays': song.play_count,
                    'likes': song.likes_count,
                })
        
        return Response({
            'period': period_label,
            'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results
        })

class AdminTopGenresReportView(APIView):
    """API hiển thị báo cáo chi tiết về top thể loại nhạc cho admin"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, format=None):
        # Lấy tham số từ request
        period = request.query_params.get('period', 'month')  # Mặc định là thống kê theo tháng
        
        # Xác định khoảng thời gian dựa trên period
        now = django.utils.timezone.now()
        if period == 'week':
            start_date = now - timedelta(days=7)
            period_label = '7 ngày qua'
        elif period == 'month':
            start_date = now - timedelta(days=30)
            period_label = '30 ngày qua'
        elif period == 'year':
            start_date = now - timedelta(days=365)
            period_label = '365 ngày qua'
        else:  # Mặc định là all
            start_date = None
            period_label = 'Tất cả thời gian'
        
        # Thống kê theo thể loại
        if start_date:
            # Lấy lượt play theo thể loại trong khoảng thời gian
            recent_plays_by_genre = {}
            for play in SongPlayHistory.objects.filter(played_at__gte=start_date).select_related('song'):
                genre = play.song.genre if play.song.genre else "Không xác định"
                recent_plays_by_genre[genre] = recent_plays_by_genre.get(genre, 0) + 1
            
            # Các thông tin khác về thể loại
            genre_stats = []
            for genre, play_count in recent_plays_by_genre.items():
                genre_songs = Song.objects.filter(genre=genre)
                top_songs = genre_songs.order_by('-play_count')[:5]
                
                genre_stats.append({
                    'genre': genre,
                    'song_count': genre_songs.count(),
                    'recent_plays': play_count,
                    'avg_song_plays': genre_songs.aggregate(Avg('play_count'))['play_count__avg'] or 0,
                    'top_songs': [
                        {'id': song.id, 'title': song.title, 'artist': song.artist, 'plays': song.play_count}
                        for song in top_songs
                    ]
                })
            
            # Sắp xếp theo lượt play gần đây
            genre_stats = sorted(genre_stats, key=lambda x: x['recent_plays'], reverse=True)
            
        else:
            # Thống kê mọi thời gian
            all_genres = set(Song.objects.values_list('genre', flat=True).distinct())
            genre_stats = []
            
            for genre in all_genres:
                if not genre:
                    continue
                
                genre_songs = Song.objects.filter(genre=genre)
                top_songs = genre_songs.order_by('-play_count')[:5]
                total_plays = genre_songs.aggregate(Sum('play_count'))['play_count__sum'] or 0

# Thêm API cho việc tải xuống bài hát nghe offline
class OfflineDownloadListView(APIView):
    """Danh sách bài hát được tải xuống offline của người dùng hiện tại"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """Lấy danh sách bài hát đã được tải xuống offline"""
        downloads = OfflineDownload.objects.filter(user=request.user)
        serializer = OfflineDownloadSerializer(downloads, many=True)
        return Response(serializer.data)
        
class OfflineDownloadView(APIView):
    """API để yêu cầu tải xuống bài hát offline"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        """Yêu cầu tải xuống một bài hát để nghe offline"""
        song_id = request.data.get('song_id')
        if not song_id:
            return Response({'error': 'Cần cung cấp ID bài hát'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Kiểm tra bài hát tồn tại
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            return Response({'error': 'Bài hát không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
            
        # Kiểm tra xem đã tải xuống trước đó chưa
        download, created = OfflineDownload.objects.get_or_create(
            user=request.user,
            song=song,
            defaults={
                'status': 'PENDING',
                'progress': 0,
                'is_active': True,
                'expiry_time': django.utils.timezone.now() + timedelta(days=30)  # Mặc định 30 ngày
            }
        )
        
        if not created:
            # Nếu đã tồn tại, cập nhật trạng thái
            if download.status in ['FAILED', 'EXPIRED']:
                download.status = 'PENDING'
                download.progress = 0
                download.is_active = True
                download.expiry_time = django.utils.timezone.now() + timedelta(days=30)
                download.save()
                
            # Trả về thông báo khác nhau tùy theo trạng thái
            if download.status == 'PENDING':
                message = 'Bài hát đã được thêm vào hàng đợi tải xuống'
            elif download.status == 'DOWNLOADING':
                message = f'Bài hát đang được tải xuống ({download.progress}%)'
            elif download.status == 'COMPLETED':
                message = 'Bài hát đã được tải xuống trước đó'
            else:
                message = f'Trạng thái tải xuống: {download.get_status_display()}'
        else:
            message = 'Đã thêm vào hàng đợi tải xuống'
            
            # Đây là nơi bạn sẽ gọi task async để tải xuống (ví dụ: Celery)
            # Trong ví dụ này, chúng ta sẽ giả lập việc tải xuống ngay lập tức
            self._process_download(download)
                
        serializer = OfflineDownloadSerializer(download)
        return Response({
            'message': message,
            'download': serializer.data
        })
        
    def _process_download(self, download):
        """Xử lý tải xuống (trong thực tế nên được xử lý bởi một task background)"""
        try:
            # Cập nhật trạng thái
            download.status = 'DOWNLOADING'
            download.progress = 0
            download.save()
            
            # Tạo thư mục lưu trữ cục bộ
            target_dir = os.path.join(settings.MEDIA_ROOT, f'offline/{download.user.id}')
            
            # Tải xuống bài hát sử dụng utility function
            success, message, file_path = download_song_for_offline(download.song, target_dir)
            
            # Cập nhật trạng thái
            if success and file_path:
                # Kiểm tra file tải xuống có hợp lệ không
                if verify_offline_song(file_path):
                    download.status = 'COMPLETED'
                    download.progress = 100
                    download.local_path = file_path
                else:
                    download.status = 'FAILED'
                    download.progress = 0
                    download.local_path = None
            else:
                download.status = 'FAILED'
                download.progress = 0
                
            download.save()
            
        except Exception as e:
            download.status = 'FAILED'
            download.save()
            print(f"Lỗi khi tải xuống: {str(e)}")
            
class DeleteOfflineDownloadView(APIView):
    """API để xóa bài hát đã tải xuống offline"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, download_id, format=None):
        """Xóa một bài hát đã tải xuống"""
        try:
            download = OfflineDownload.objects.get(id=download_id, user=request.user)
        except OfflineDownload.DoesNotExist:
            return Response({'error': 'Không tìm thấy bài hát đã tải xuống'}, status=status.HTTP_404_NOT_FOUND)
            
        # Trong thực tế, bạn sẽ xóa file khỏi bộ nhớ cục bộ ở đây
        # Nhưng trong ví dụ này, chúng ta chỉ cập nhật trạng thái
        download.is_active = False
        download.save()
        
        return Response({'message': 'Đã xóa bài hát khỏi danh sách tải xuống offline'})
    
class OfflineDownloadStatusView(APIView):
    """API để kiểm tra trạng thái tải xuống"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, download_id, format=None):
        """Kiểm tra trạng thái tải xuống của một bài hát"""
        try:
            download = OfflineDownload.objects.get(id=download_id, user=request.user)
        except OfflineDownload.DoesNotExist:
            return Response({'error': 'Không tìm thấy bài hát đã tải xuống'}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = OfflineDownloadSerializer(download)
        return Response(serializer.data)