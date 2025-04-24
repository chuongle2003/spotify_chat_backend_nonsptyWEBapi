from rest_framework import serializers
from .models import User
from music.models import Song, Playlist
from music.serializers import SongBasicSerializer, PlaylistBasicSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'bio')
        extra_kwargs = {'password': {'write_only': True}}

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'avatar', 'bio')
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class PublicUserSerializer(serializers.ModelSerializer):
    """Serializer cho việc hiển thị thông tin công khai của người dùng."""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar', 'bio')
        # Chỉ hiển thị các trường công khai, không hiển thị email và các thông tin cá nhân khác

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer cho việc quản lý người dùng."""
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'avatar', 'bio', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'can_manage_users', 
            'can_manage_content', 'can_manage_playlists',
            'followers_count', 'following_count'
        )
        read_only_fields = ('date_joined', 'last_login')
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()

class MinimalUserSerializer(serializers.ModelSerializer):
    """Serializer cho hiển thị thông tin tối thiểu của người dùng trong các quan hệ"""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar')

class CompleteUserSerializer(serializers.ModelSerializer):
    """Serializer cho hiển thị toàn bộ thông tin của người dùng"""
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    favorite_songs = serializers.SerializerMethodField()
    playlists = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'avatar', 'bio', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'can_manage_users', 
            'can_manage_content', 'can_manage_playlists',
            'followers_count', 'following_count', 'followers', 'following',
            'favorite_songs', 'playlists', 'activities', 'created_at', 'updated_at'
        )
        read_only_fields = ('date_joined', 'last_login', 'created_at', 'updated_at')
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()
    
    def get_followers(self, obj):
        return MinimalUserSerializer(obj.followers.all(), many=True).data
    
    def get_following(self, obj):
        return MinimalUserSerializer(obj.following.all(), many=True).data
    
    def get_favorite_songs(self, obj):
        return SongBasicSerializer(obj.favorite_songs.all(), many=True).data
    
    def get_playlists(self, obj):
        return PlaylistBasicSerializer(obj.playlists.all(), many=True).data
    
    def get_activities(self, obj):
        from music.serializers import UserActivitySerializer
        activities = obj.activities.all()[:10]  # Get 10 most recent activities
        return UserActivitySerializer(activities, many=True).data 