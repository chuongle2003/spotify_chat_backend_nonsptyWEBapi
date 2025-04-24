from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Thêm lại trường favorite_songs và các quan hệ khác đã xóa tạm thời
    favorite_songs = models.ManyToManyField('music.Song', related_name='favorited_by', blank=True)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    
    # Thêm các trường quyền
    can_manage_users = models.BooleanField(default=False, verbose_name='Có thể quản lý người dùng')
    can_manage_content = models.BooleanField(default=False, verbose_name='Có thể quản lý nội dung')
    can_manage_playlists = models.BooleanField(default=False, verbose_name='Có thể quản lý playlist')
    
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
    def is_user_manager(self):
        return self.is_staff and self.can_manage_users
        
    @property
    def is_content_manager(self):
        return self.is_staff and self.can_manage_content
        
    @property
    def is_playlist_manager(self):
        return self.is_staff and self.can_manage_playlists
