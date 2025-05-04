from rest_framework import serializers
from .models import User, UserConnection
from music.models import Song, Playlist
from music.serializers import SongBasicSerializer, PlaylistBasicSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from typing import Dict, Any, cast
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser

UserModel = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Validate email
        email = attrs.get('email', '')
        if not email.endswith('@gmail.com'):
            raise serializers.ValidationError({"email": "Email phải là địa chỉ Gmail (@gmail.com)."})
        
        # Validate password
        password = attrs.get('password', '')
        if len(password) < 8:
            raise serializers.ValidationError({"password": "Mật khẩu phải có ít nhất 8 ký tự."})
        
        # Lấy token data từ parent class
        data: Dict[str, Any] = super().validate(attrs)
        
        # Thêm thông tin user vào response
        user = cast(AbstractBaseUser, self.user)
        if user is not None:
            avatar = getattr(user, 'avatar', None)
            avatar_url = avatar.url if avatar else None
            
            user_data = {
                'id': user.pk,
                'username': getattr(user, 'username', ''),
                'email': getattr(user, 'email', ''),
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'avatar': avatar_url,
                'bio': getattr(user, 'bio', ''),
                'is_admin': getattr(user, 'is_admin', False)
            }
            data['user'] = user_data
        
        return data

class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'avatar', 'bio', 'is_admin')
        extra_kwargs = {'password': {'write_only': True}}

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 
                 'last_name', 'avatar', 'bio')
    
    def validate_email(self, value):
        """
        Kiểm tra email phải là địa chỉ Gmail.
        """
        if not value.endswith('@gmail.com'):
            raise serializers.ValidationError("Email phải là địa chỉ Gmail (@gmail.com).")
        return value
    
    def validate_password(self, value):
        """
        Kiểm tra mật khẩu có đủ độ dài và độ phức tạp không.
        """
        if len(value) < 8:
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class AdminUserCreateSerializer(serializers.ModelSerializer):
    """Serializer cho phép Admin tạo người dùng mới với các quyền cụ thể."""
    password = serializers.CharField(write_only=True)
    is_admin = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 
                 'last_name', 'avatar', 'bio', 'is_admin', 'is_active')
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        # Đặt giá trị mặc định nếu không được cung cấp
        if 'is_admin' not in validated_data:
            validated_data['is_admin'] = False
        if 'is_active' not in validated_data:
            validated_data['is_active'] = True
            
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
            'avatar', 'bio', 'is_active', 'is_admin',
            'date_joined', 'last_login', 'followers_count', 'following_count'
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
            'avatar', 'bio', 'is_active', 'is_admin',
            'date_joined', 'last_login', 'followers_count', 'following_count', 
            'followers', 'following', 'favorite_songs', 'playlists', 
            'activities', 'created_at', 'updated_at'
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

class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer cho chức năng quên mật khẩu."""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """
        Kiểm tra email phải là gmail và tồn tại trong hệ thống.
        """
        if not value.endswith('@gmail.com'):
            raise serializers.ValidationError("Email phải là địa chỉ Gmail (@gmail.com).")
        
        # Kiểm tra email có tồn tại trong database không
        User = get_user_model()
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Không tiết lộ liệu email tồn tại hay không vì lý do bảo mật
            # Chúng ta sẽ xử lý trong view
            pass
            
        return value

class VerifyPasswordResetTokenSerializer(serializers.Serializer):
    """Serializer cho chức năng xác minh token reset mật khẩu."""
    email = serializers.EmailField()
    token = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)
    
    def validate_email(self, value):
        """
        Kiểm tra email phải là gmail và tồn tại trong hệ thống.
        """
        if not value.endswith('@gmail.com'):
            raise serializers.ValidationError("Email phải là địa chỉ Gmail (@gmail.com).")
        
        # Kiểm tra email có tồn tại trong database không
        User = get_user_model()
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email không tồn tại trong hệ thống.")
            
        return value
    
    def validate_token(self, value):
        # Chỉ chấp nhận token có 6 ký tự số
        if not value.isdigit():
            raise serializers.ValidationError("Token phải chứa 6 ký tự số.")
        return value
    
    def validate_new_password(self, value):
        # Kiểm tra độ mạnh của mật khẩu
        if len(value) < 8:
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")
        return value

class UserConnectionSerializer(serializers.ModelSerializer):
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    requester_avatar = serializers.SerializerMethodField()
    receiver_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = UserConnection
        fields = ['id', 'requester', 'receiver', 'requester_username', 'receiver_username', 
                  'requester_avatar', 'receiver_avatar', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_requester_avatar(self, obj):
        if hasattr(obj.requester, 'avatar') and obj.requester.avatar:
            return obj.requester.avatar.url
        return None
        
    def get_receiver_avatar(self, obj):
        if hasattr(obj.receiver, 'avatar') and obj.receiver.avatar:
            return obj.receiver.avatar.url
        return None 