from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ValidationError
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer, PublicUserSerializer, AdminUserSerializer, CompleteUserSerializer, CustomTokenObtainPairSerializer, AdminUserCreateSerializer
from rest_framework.views import APIView
from .permissions import IsAdminUser, IsOwnerOrReadOnly, ReadOnly
import logging
from rest_framework_simplejwt.views import TokenObtainPairView

logger = logging.getLogger(__name__)

# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        elif self.action == 'list':
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        user_to_follow = self.get_object()
        user = request.user
        
        if user_to_follow == user:
            return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.following.add(user_to_follow)
        return Response({'status': 'Successfully followed user'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        user_to_unfollow = self.get_object()
        user = request.user
        
        user.following.remove(user_to_unfollow)
        return Response({'status': 'Successfully unfollowed user'}, status=status.HTTP_200_OK)

class AdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin-only operations on users
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AdminUserCreateSerializer
        return AdminUserSerializer
    
    @action(detail=True, methods=['get'])
    def complete(self, request, pk=None):
        """Get all details for a user including related data"""
        user = self.get_object()
        serializer = CompleteUserSerializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        action = "activated" if user.is_active else "deactivated"
        logger.info(f"User {user.username} {action} by {request.user.username}")
        
        return Response({'status': f'User {action}'})
    
    @action(detail=True, methods=['post'])
    def toggle_admin(self, request, pk=None):
        user = self.get_object()
        user.is_admin = not user.is_admin
        user.save()
        
        action = "granted admin access" if user.is_admin else "removed admin access"
        logger.info(f"User {user.username} {action} by {request.user.username}")
        
        return Response({'status': f'User {action}'})
    
    def create(self, request, *args, **kwargs):
        """Create a new user with admin privileges"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        logger.info(f"New user {user.username} created by admin {request.user.username}")
        
        return Response(
            AdminUserSerializer(user, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a user's information"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        logger.info(f"User {user.username} updated by admin {request.user.username}")
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a user"""
        instance = self.get_object()
        username = instance.username
        
        # Ngăn admin xóa chính mình
        if instance == request.user:
            return Response(
                {"error": "You cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        
        logger.info(f"User {username} deleted by admin {request.user.username}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)

# Thêm APIView mới để xem danh sách user mà không cần xác thực
class PublicUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]

# Thêm view riêng để đăng ký
class RegisterView(generics.CreateAPIView):
    """
    Endpoint đơn giản để đăng ký người dùng mới.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Trả về thông tin người dùng không bao gồm password
        return Response(
            UserSerializer(user, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            # Lấy refresh token từ request
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate và blacklist token
            try:
                token = RefreshToken(refresh_token)
                # Kiểm tra token có thuộc về user hiện tại không
                if token.payload.get('user_id') != request.user.id:
                    raise ValidationError("Token does not belong to current user")
                
                token.blacklist()
                
                # Log thông tin đăng xuất
                logger.info(f"User {request.user.username} logged out successfully")
                
                return Response(
                    {"message": "Successfully logged out"},
                    status=status.HTTP_200_OK
                )
            except TokenError as te:
                # Log lỗi token
                logger.error(f"Invalid refresh token provided by user {request.user.username}: {str(te)}")
                return Response(
                    {"error": "Invalid or expired refresh token"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except ValidationError as ve:
                logger.error(f"Token validation error for user {request.user.username}: {str(ve)}")
                return Response(
                    {"error": str(ve)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # Log lỗi không xác định
            logger.error(f"Logout error for user {request.user.username}: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
