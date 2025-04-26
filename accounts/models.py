from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Relationships
    favorite_songs = models.ManyToManyField('music.Song', related_name='favorited_by', blank=True)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    
    # Chỉ còn 1 quyền duy nhất: admin hoặc không phải admin
    is_admin = models.BooleanField(default=False, verbose_name='Is Admin User')
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return self.email
    
    @property
    def has_admin_access(self):
        """Check if user has admin access"""
        return self.is_superuser or self.is_admin
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            # Nếu user là superuser, tự động set is_admin = True
            self.is_admin = True
            self.is_staff = True
        elif self.is_admin:
            # Nếu user là admin, tự động grant các quyền cần thiết
            self.is_staff = True
        super().save(*args, **kwargs)

class PasswordResetToken(models.Model):
    """Model for password reset tokens."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            # Tạo token ngẫu nhiên gồm 6 chữ số
            self.token = ''.join(random.choices(string.digits, k=6))
        
        if not self.expires_at:
            # Token hết hạn sau 15 phút
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
            
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if token is valid."""
        return not self.is_used and self.expires_at > timezone.now()
    
    @classmethod
    def generate_token(cls, user):
        """Generate a new token for the user."""
        # Đánh dấu tất cả token cũ của user là đã sử dụng
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Tạo token mới
        return cls.objects.create(user=user)
