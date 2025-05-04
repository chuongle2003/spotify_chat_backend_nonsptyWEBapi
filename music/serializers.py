from rest_framework import serializers
from .models import (
    Song, Playlist, Album, Genre, Rating, Comment, SongPlayHistory, 
    SearchHistory, UserActivity, LyricLine, Artist, Queue, QueueItem, UserStatus, Message, CollaboratorRole, PlaylistEditHistory,
    UserRecommendation, OfflineDownload
)
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'bio')
        read_only_fields = ('id',)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'bio')
        read_only_fields = ('id',)

class SongBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Song model when referenced in other serializers"""
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Song
        fields = ('id', 'title', 'artist', 'cover_image', 'duration')
        
    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.cover_image.url}"
        return None

class PlaylistBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Playlist model when referenced in other serializers"""
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = ('id', 'name', 'is_public', 'cover_image')
        
    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.cover_image.url}"
        return None

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for referencing in music models"""
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar')

class ArtistSerializer(serializers.ModelSerializer):
    """Serializer for Artist model"""
    class Meta:
        model = Artist
        fields = ('id', 'name', 'bio', 'image')

class GenreBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Genre model"""
    class Meta:
        model = Genre
        fields = ('id', 'name', 'image')

class AlbumBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Album model"""
    class Meta:
        model = Album
        fields = ('id', 'title', 'artist', 'cover_image', 'release_date')

class SongSerializer(serializers.ModelSerializer):
    uploaded_by = UserBasicSerializer(read_only=True)
    audio_file = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Song
        fields = ('id', 'title', 'artist', 'album', 'duration', 'audio_file', 
                 'cover_image', 'genre', 'likes_count', 'play_count', 
                 'uploaded_by', 'created_at', 'release_date')
                 
    def get_audio_file(self, obj):
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.audio_file.url}"
        return None
        
    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.cover_image.url}"
        return None

class SongDetailSerializer(serializers.ModelSerializer):
    uploaded_by = UserBasicSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    audio_file = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Song
        fields = ('id', 'title', 'artist', 'album', 'duration', 'audio_file', 
                 'cover_image', 'genre', 'likes_count', 'play_count', 
                 'uploaded_by', 'created_at', 'lyrics', 'release_date', 'comments_count')
                 
    def get_comments_count(self, obj):
        return obj.comments.count()
        
    def get_audio_file(self, obj):
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.audio_file.url}"
        return None
        
    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.cover_image.url}"
        return None

class PlaylistSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    is_collaborative = serializers.BooleanField(read_only=True)
    collaborators_count = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ['id', 'name', 'user', 'description', 'is_public', 'cover_image', 
                  'created_at', 'updated_at', 'is_collaborative', 'collaborators_count']
        read_only_fields = ['user', 'created_at', 'updated_at', 'collaborators_count']

    def get_collaborators_count(self, obj):
        return obj.collaborators.count()

class PlaylistDetailSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    songs = SongSerializer(many=True, read_only=True)
    followers_count = serializers.SerializerMethodField()
    is_collaborative = serializers.BooleanField(read_only=True)
    collaborators = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ['id', 'name', 'user', 'description', 'is_public', 'cover_image', 
                  'songs', 'created_at', 'updated_at', 'followers_count', 
                  'is_collaborative', 'collaborators']
        read_only_fields = ['user', 'created_at', 'updated_at', 'followers_count']

    def get_followers_count(self, obj):
        return obj.followers.count()
        
    def get_collaborators(self, obj):
        if not obj.is_collaborative:
            return []
        return CollaboratorRoleSerializer(
            obj.role_assignments.all(), many=True, context=self.context
        ).data

class CollaboratorRoleSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    playlist = serializers.PrimaryKeyRelatedField(read_only=True)
    added_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = CollaboratorRole
        fields = ['id', 'user', 'playlist', 'role', 'added_by', 'added_at']
        read_only_fields = ['added_by', 'added_at']

class CollaboratorRoleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollaboratorRole
        fields = ['user', 'playlist', 'role']
        
    def validate(self, data):
        # Kiểm tra xem playlist có phải collaborative không
        playlist = data.get('playlist')
        if not playlist.is_collaborative:
            raise serializers.ValidationError(
                "Không thể thêm cộng tác viên vào playlist không phải là collaborative")
                
        # Kiểm tra xem user đã là cộng tác viên của playlist chưa
        user = data.get('user')
        if CollaboratorRole.objects.filter(playlist=playlist, user=user).exists():
            raise serializers.ValidationError(
                "Người dùng này đã là cộng tác viên của playlist")
                
        # Không thể thêm chủ sở hữu playlist làm cộng tác viên
        if user == playlist.user:
            raise serializers.ValidationError(
                "Không thể thêm chủ sở hữu playlist làm cộng tác viên")
                
    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.cover_image.url}"
        return None

class UserActivitySerializer(serializers.ModelSerializer):
    song = SongBasicSerializer(read_only=True)
    playlist = PlaylistBasicSerializer(read_only=True)
    target_user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ('id', 'activity_type', 'song', 'playlist', 'target_user', 'timestamp')

class CommentSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'user', 'song', 'content', 'created_at', 'parent', 'replies')
        read_only_fields = ('id', 'created_at', 'replies')
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def get_replies(self, obj):
        if obj.parent is None:  # Chỉ lấy replies cho comment gốc
            replies = obj.replies.all()
            return CommentSerializer(replies, many=True, context=self.context).data
        return []

class RatingSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = ('id', 'user', 'song', 'rating', 'created_at')
        read_only_fields = ('id', 'created_at')
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class AlbumSerializer(serializers.ModelSerializer):
    songs_count = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Album
        fields = ('id', 'title', 'artist', 'release_date', 'cover_image', 'description', 'created_at', 'songs_count')
    
    def get_songs_count(self, obj):
        return Song.objects.filter(album=obj.title).count()
        
    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.cover_image.url}"
        return None

class AlbumDetailSerializer(serializers.ModelSerializer):
    songs = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Album
        fields = ('id', 'title', 'artist', 'release_date', 'cover_image', 'description', 'created_at', 'songs')
    
    def get_songs(self, obj):
        songs = Song.objects.filter(album=obj.title)
        context = self.context
        return SongSerializer(songs, many=True, context=context).data
    
    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            # Nếu không có request, sử dụng SITE_URL từ settings
            return f"{settings.SITE_URL}{obj.cover_image.url}"
        return None

class GenreSerializer(serializers.ModelSerializer):
    songs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Genre
        fields = ('id', 'name', 'description', 'image', 'songs_count')
    
    def get_songs_count(self, obj):
        return Song.objects.filter(genre=obj.name).count()

class GenreDetailSerializer(serializers.ModelSerializer):
    top_songs = serializers.SerializerMethodField()
    top_artists = serializers.SerializerMethodField()
    
    class Meta:
        model = Genre
        fields = ('id', 'name', 'description', 'image', 'top_songs', 'top_artists')
    
    def get_top_songs(self, obj):
        songs = Song.objects.filter(genre=obj.name).order_by('-play_count')[:10]
        return SongSerializer(songs, many=True).data
        
    def get_top_artists(self, obj):
        # Lấy nghệ sĩ nổi bật trong thể loại này
        artists = {}
        for song in Song.objects.filter(genre=obj.name):
            if song.artist in artists:
                artists[song.artist] += 1
            else:
                artists[song.artist] = 1
        
        # Trả về tên nghệ sĩ
        top_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{'name': artist[0], 'songs_count': artist[1]} for artist in top_artists]

class SongPlayHistorySerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    
    class Meta:
        model = SongPlayHistory
        fields = ('id', 'user', 'song', 'played_at')
        read_only_fields = ('user', 'played_at')

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ('id', 'query', 'timestamp')
        read_only_fields = ('user', 'timestamp') 

class LyricLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = LyricLine
        fields = ('id', 'song', 'timestamp', 'text')

class QueueItemSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    
    class Meta:
        model = QueueItem
        fields = ('id', 'position', 'song', 'added_at')
        read_only_fields = ('id', 'added_at')

class QueueSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Queue
        fields = ('id', 'items', 'updated_at')
        read_only_fields = ('id', 'updated_at')
    
    def get_items(self, obj):
        queue_items = QueueItem.objects.filter(queue=obj).order_by('position')
        return QueueItemSerializer(queue_items, many=True).data

class UserStatusSerializer(serializers.ModelSerializer):
    currently_playing = SongBasicSerializer(read_only=True)
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = UserStatus
        fields = ('id', 'user', 'currently_playing', 'status_text', 'is_listening', 'updated_at')
        read_only_fields = ('id', 'updated_at')

class MessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    receiver = UserBasicSerializer(read_only=True)
    shared_song = SongBasicSerializer(read_only=True)
    shared_playlist = PlaylistBasicSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ('id', 'sender', 'receiver', 'content', 'timestamp', 'is_read', 
                 'message_type', 'shared_song', 'shared_playlist', 'attachment', 'image', 'voice_note')
        read_only_fields = ('id', 'timestamp', 'is_read') 

class PlaylistEditHistorySerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    related_song = SongBasicSerializer(read_only=True)
    related_user = UserBasicSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = PlaylistEditHistory
        fields = ['id', 'playlist', 'user', 'action', 'action_display', 'timestamp', 
                  'details', 'related_song', 'related_user']
        read_only_fields = ['playlist', 'user', 'action', 'timestamp', 
                          'details', 'related_song', 'related_user']


class CollaborativePlaylistCreateSerializer(serializers.ModelSerializer):
    """Serializer để tạo Collaborative Playlist mới"""
    initial_collaborators = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Playlist
        fields = ['name', 'description', 'is_public', 'cover_image', 
                  'is_collaborative', 'initial_collaborators']
        
    def validate(self, data):
        # Đảm bảo is_collaborative = True
        data['is_collaborative'] = True
        return data
        
    def create(self, validated_data):
        initial_collaborators = validated_data.pop('initial_collaborators', [])
        
        # Tạo playlist
        playlist = Playlist.objects.create(**validated_data)
        
        # Thêm người cộng tác ban đầu (nếu có)
        user_model = get_user_model()
        for user_id in initial_collaborators:
            try:
                collaborator = user_model.objects.get(id=user_id)
                # Bỏ qua nếu người dùng là chủ sở hữu
                if collaborator != playlist.user:
                    CollaboratorRole.objects.create(
                        user=collaborator,
                        playlist=playlist,
                        role='EDITOR',
                        added_by=playlist.user
                    )
            except user_model.DoesNotExist:
                pass
        
        # Ghi nhật ký hành động
        PlaylistEditHistory.log_action(
            playlist=playlist,
            user=playlist.user,
            action='CREATE',
            details={'name': playlist.name, 'collaborative': True}
        )
        
        return playlist 

class AdminCollaborativePlaylistListSerializer(serializers.ModelSerializer):
    owner = UserBasicSerializer(read_only=True)
    collaborator_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = ['id', 'name', 'description', 'owner', 'cover_image', 'created_at', 'is_collaborative', 'collaborator_count']
    
    def get_collaborator_count(self, obj):
        return obj.collaborators.count()

class AdminCollaboratorDetailSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = CollaboratorRole
        fields = ['id', 'user', 'role', 'added_at']

class AdminCollaboratorAddSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=CollaboratorRole.ROLE_CHOICES)
    
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value

class AdminCollaboratorRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=CollaboratorRole.ROLE_CHOICES)

class AdminRestorePlaylistSerializer(serializers.Serializer):
    history_id = serializers.IntegerField()
    
    def validate_history_id(self, value):
        try:
            PlaylistEditHistory.objects.get(id=value)
        except PlaylistEditHistory.DoesNotExist:
            raise serializers.ValidationError("History entry does not exist")
        return value 

class UserRecommendationSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    
    class Meta:
        model = UserRecommendation
        fields = ['id', 'user', 'song', 'score', 'created_at']
        read_only_fields = ['user', 'created_at']

class OfflineDownloadSerializer(serializers.ModelSerializer):
    song_details = SongSerializer(source='song', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OfflineDownload
        fields = [
            'id', 'user', 'song', 'song_details', 'status', 'status_display', 
            'progress', 'local_path', 'download_time', 'expiry_time', 
            'is_active', 'is_available'
        ]
        read_only_fields = ['user', 'download_time', 'status_display', 'is_available']
        
    def create(self, validated_data):
        # Tự động gán user hiện tại khi tạo mới
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data) 