from rest_framework import serializers
from .models import Song, Playlist, Album, Genre, Rating, Comment, SongPlayHistory, SearchHistory, UserActivity
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
        fields = ('id', 'title', 'artist')

class PlaylistBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Playlist model when referenced in other serializers"""
    class Meta:
        model = Playlist
        fields = ('id', 'name', 'is_public')

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for referencing in music models"""
    class Meta:
        model = User
        fields = ('id', 'username')

class SongSerializer(serializers.ModelSerializer):
    uploaded_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Song
        fields = ('id', 'title', 'artist', 'album', 'duration', 'audio_file', 
                 'cover_image', 'genre', 'likes_count', 'play_count', 
                 'uploaded_by', 'created_at')

class SongDetailSerializer(serializers.ModelSerializer):
    uploaded_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Song
        fields = ('id', 'title', 'artist', 'album', 'duration', 'audio_file', 
                 'cover_image', 'genre', 'likes_count', 'play_count', 
                 'uploaded_by', 'created_at', 'lyrics')

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
    
    class Meta:
        model = Comment
        fields = ('id', 'user', 'song', 'content', 'created_at')
        read_only_fields = ('id', 'created_at')
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

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
    class Meta:
        model = Album
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class SongPlayHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SongPlayHistory
        fields = '__all__'
        read_only_fields = ('user', 'played_at')

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'
        read_only_fields = ('user', 'timestamp') 