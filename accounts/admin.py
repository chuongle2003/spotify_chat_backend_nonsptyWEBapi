from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User as AuthUser
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from .models import User, PasswordResetToken, UserConnection

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_avatar', 'is_admin', 'is_active', 'get_status', 'date_joined')
    list_filter = ('is_admin', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = ['activate_users', 'deactivate_users']
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Thông tin cá nhân', {'fields': ('first_name', 'last_name', 'avatar', 'bio')}),
        ('Quyền hạn và trạng thái', {'fields': ('is_active', 'is_admin', 'is_superuser')}),
        ('Thống kê', {'fields': ('get_following_count', 'get_followers_count', 'get_favorite_songs_count', 'has_chat_restriction')})
    )
    readonly_fields = ('get_following_count', 'get_followers_count', 'get_favorite_songs_count', 'has_chat_restriction')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active', 'is_admin'),
        }),
    )
    
    def get_avatar(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="30" height="30" style="border-radius: 50%;" />', obj.avatar.url)
        return format_html('<span style="color:gray;">Không có</span>')
    get_avatar.short_description = 'Ảnh đại diện'
    
    def get_status(self, obj):
        # Kiểm tra xem người dùng có bị hạn chế chat không
        has_restriction = hasattr(obj, 'chat_restrictions') and obj.chat_restrictions.filter(is_active=True).exists()
        
        if not obj.is_active:
            return format_html('<span style="color:red;">Vô hiệu hoá</span>')
        elif has_restriction:
            return format_html('<span style="color:orange;">Đã hạn chế chat</span>')
        return format_html('<span style="color:green;">Hoạt động</span>')
    get_status.short_description = 'Trạng thái'
    
    def get_following_count(self, obj):
        return obj.following.count()
    get_following_count.short_description = 'Đang theo dõi'
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    get_followers_count.short_description = 'Người theo dõi'
    
    def get_favorite_songs_count(self, obj):
        return obj.favorite_songs.count()
    get_favorite_songs_count.short_description = 'Bài hát yêu thích'
    
    def has_chat_restriction(self, obj):
        has_restriction = hasattr(obj, 'chat_restrictions') and obj.chat_restrictions.filter(is_active=True).exists()
        if has_restriction:
            return format_html('<span style="color:red;">Có</span>')
        return format_html('<span style="color:green;">Không</span>')
    has_chat_restriction.short_description = 'Hạn chế chat'
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Kích hoạt tài khoản người dùng đã chọn"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Vô hiệu hoá tài khoản người dùng đã chọn"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('following', 'followers', 'favorite_songs')
        return queryset

class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used', 'is_valid_token')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__username', 'token')
    ordering = ('-created_at',)
    readonly_fields = ('token', 'created_at', 'expires_at', 'is_valid_token')
    
    def is_valid_token(self, obj):
        if obj.is_valid:
            return format_html('<span style="color:green;">Còn hiệu lực</span>')
        return format_html('<span style="color:red;">Hết hiệu lực</span>')
    is_valid_token.short_description = 'Còn hiệu lực'
    
@admin.register(UserConnection)
class UserConnectionAdmin(admin.ModelAdmin):
    list_display = ('requester', 'receiver', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('requester__username', 'requester__email', 'receiver__username', 'receiver__email')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('requester', 'receiver')
        return queryset

admin.site.register(User, UserAdmin)
admin.site.register(PasswordResetToken, PasswordResetTokenAdmin)
