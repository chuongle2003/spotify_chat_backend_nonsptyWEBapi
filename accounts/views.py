from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer, PublicUserSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
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
        return Response(status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        user_to_unfollow = self.get_object()
        user = request.user
        
        user.following.remove(user_to_unfollow)
        return Response(status=status.HTTP_200_OK)

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

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()  # Đánh dấu token đã sử dụng
            
            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )
