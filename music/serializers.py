from rest_framework import serializers
from .models import (
    Song, Playlist, Album, Genre, Rating, Comment, SongPlayHistory, 
    SearchHistory, UserActivity, LyricLine, Artist, Queue, QueueItem, UserStatus, Message
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
    class Meta:
        model = Song
        fields = ('id', 'title', 'artist', 'cover_image', 'duration')

class PlaylistBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Playlist model when referenced in other serializers"""
    class Meta:
        model = Playlist
        fields = ('id', 'name', 'is_public', 'cover_image')

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
    
    class Meta:
        model = Song
        fields = ('id', 'title', 'artist', 'album', 'duration', 'audio_file', 
                 'cover_image', 'genre', 'likes_count', 'play_count', 
                 'uploaded_by', 'created_at', 'release_date')

class SongDetailSerializer(serializers.ModelSerializer):
    uploaded_by = UserBasicSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Song
        fields = ('id', 'title', 'artist', 'album', 'duration', 'audio_file', 
                 'cover_image', 'genre', 'likes_count', 'play_count', 
                 'uploaded_by', 'created_at', 'lyrics', 'release_date', 'comments_count')
                 
    def get_comments_count(self, obj):
        return obj.comments.count()

class PlaylistSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    songs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = ('id', 'name', 'description', 'is_public', 'cover_image', 
                 'user', 'songs_count', 'created_at', 'updated_at')
        
    def get_songs_count(self, obj):
        return obj.songs.count()

class PlaylistDetailSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    songs = SongSerializer(many=True, read_only=True)
    followers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = ('id', 'name', 'description', 'is_public', 'cover_image', 
                 'user', 'songs', 'followers_count', 'created_at', 'updated_at')
        
    def get_followers_count(self, obj):
        return obj.followers.count()

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
    
    class Meta:
        model = Album
        fields = ('id', 'title', 'artist', 'release_date', 'cover_image', 'description', 'created_at', 'songs_count')
    
    def get_songs_count(self, obj):
        return Song.objects.filter(album=obj.title).count()

class AlbumDetailSerializer(serializers.ModelSerializer):
    songs = serializers.SerializerMethodField()
    
    class Meta:
        model = Album
        fields = ('id', 'title', 'artist', 'release_date', 'cover_image', 'description', 'created_at', 'songs')
    
    def get_songs(self, obj):
        songs = Song.objects.filter(album=obj.title)
        return SongSerializer(songs, many=True).data

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
    song = SongBasicSerializer(read_only=True)
    
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