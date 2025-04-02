from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    has_spotify = models.BooleanField(default=False)
    
    # Thêm lại trường favorite_songs và các quan hệ khác đã xóa tạm thời
    favorite_songs = models.ManyToManyField('music.Song', related_name='favorited_by', blank=True)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    
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
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return self.username
