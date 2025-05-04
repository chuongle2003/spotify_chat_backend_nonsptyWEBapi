from django.contrib import admin
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Song, Playlist, Album, Genre, Comment, Rating, OfflineDownload  # Thêm OfflineDownload

# Lỗi xảy ra ở dòng này: @admin.register(User)
# User đang là một string chứ không phải là một model

# Sửa lại bằng cách import User đúng cách:
User = get_user_model()  # Lấy model User từ settings

# Đăng ký các model khác
@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'uploaded_by', 'created_at')
    search_fields = ('title', 'artist')
    list_filter = ('genre', 'created_at')

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_public', 'created_at')

# Các model khác
@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'release_date')

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'created_at')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'rating', 'created_at')

@admin.register(OfflineDownload)
class OfflineDownloadAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'status', 'progress', 'download_time', 'expiry_time', 'is_active')
    list_filter = ('status', 'is_active', 'download_time')
    search_fields = ('user__username', 'song__title')
    date_hierarchy = 'download_time'