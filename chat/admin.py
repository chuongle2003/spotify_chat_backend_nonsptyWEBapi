from django.contrib import admin
from .models import Message, MessageReport, ChatRestriction

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'message_type', 'content_status', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')
    list_filter = ('timestamp', 'message_type', 'content_status')
    ordering = ('-timestamp',)
    readonly_fields = ('sender', 'receiver', 'timestamp', 'is_read')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('sender', 'receiver', 'timestamp', 'is_read')
        }),
        ('Nội dung tin nhắn', {
            'fields': ('content', 'message_type')
        }),
        ('Tập tin đính kèm', {
            'fields': ('attachment', 'image', 'voice_note', 'shared_song', 'shared_playlist')
        }),
        ('Kiểm duyệt', {
            'fields': ('content_status', 'review_note', 'reviewed_by', 'reviewed_at')
        }),
    )

@admin.register(MessageReport)
class MessageReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'reporter', 'reason', 'status', 'timestamp')
    list_filter = ('status', 'reason', 'timestamp')
    search_fields = ('reporter__username', 'message__content', 'description')
    ordering = ('-timestamp',)
    readonly_fields = ('message', 'reporter', 'timestamp')
    
    fieldsets = (
        ('Thông tin báo cáo', {
            'fields': ('message', 'reporter', 'reason', 'description', 'timestamp')
        }),
        ('Xử lý báo cáo', {
            'fields': ('status', 'handled_by', 'handled_at', 'action_taken')
        }),
    )

@admin.register(ChatRestriction)
class ChatRestrictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'restriction_type', 'is_active', 'created_at', 'expires_at')
    list_filter = ('restriction_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'reason')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Thông tin hạn chế', {
            'fields': ('user', 'restriction_type', 'reason', 'created_at')
        }),
        ('Thời hạn và trạng thái', {
            'fields': ('is_active', 'expires_at', 'created_by')
        }),
    )