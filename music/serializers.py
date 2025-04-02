from rest_framework import serializers
from .models import Song, Playlist, Album, Genre, Rating, Comment, SongPlayHistory, SearchHistory
from django.contrib.auth import get_user_model

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

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = '__all__'
        read_only_fields = ('uploaded_by', 'created_at', 'play_count', 'likes_count')

class PlaylistSerializer(serializers.ModelSerializer):
    songs = SongSerializer(many=True, read_only=True)
    
    class Meta:
        model = Playlist
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

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