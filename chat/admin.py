from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Q
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Message, MessageReport, ChatRestriction, Conversation

# Thêm Admin Site với Dashboard tùy chỉnh
class ChatAdminSite(admin.AdminSite):
    site_header = "Quản lý Chat"
    site_title = "Chat Administration"
    index_title = "Tổng quan hệ thống Chat"
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('chat_stats/', self.admin_view(self.chat_stats_view), name='chat_stats'),
        ]
        return custom_urls + urls
    
    def chat_stats_view(self, request):
        # Thống kê trong 7 ngày gần nhất
        now = timezone.now()
        days_ago_7 = now - timedelta(days=7)
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        total_conversations = Conversation.objects.count()
        total_messages = Message.objects.count()
        
        # Thống kê tin nhắn theo ngày
        messages_by_day = (
            Message.objects.filter(timestamp__gte=days_ago_7)
            .extra({'day': "to_char(timestamp, 'YYYY-MM-DD')"})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        
        # Tin nhắn chưa đọc
        unread_messages = Message.objects.filter(is_read=False).count()
        
        # Báo cáo chưa xử lý
        pending_reports = MessageReport.objects.filter(status='PENDING').count()
        
        data = {
            'total_users': total_users,
            'active_users': active_users,
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'unread_messages': unread_messages,
            'pending_reports': pending_reports,
            'messages_by_day': list(messages_by_day),
        }
        
        return JsonResponse(data)

# Đăng ký các model vào admin site mặc định
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'messages_count', 'last_activity', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('participants__username', 'participants__email')
    readonly_fields = ('created_at', 'updated_at', 'messages_count', 'last_activity')
    
    def get_participants(self, obj):
        participants = obj.participants.all()
        return ", ".join([user.username for user in participants])
    get_participants.short_description = 'Người tham gia'
    
    def messages_count(self, obj):
        return obj.messages.count()
    messages_count.short_description = 'Số tin nhắn'
    
    def last_activity(self, obj):
        last_msg = obj.last_message
        if last_msg:
            return last_msg.timestamp
        return obj.updated_at
    last_activity.short_description = 'Hoạt động cuối'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('participants')
        return queryset

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'message_type', 'content_short', 'content_status', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')
    list_filter = ('timestamp', 'message_type', 'content_status', 'is_read')
    ordering = ('-timestamp',)
    readonly_fields = ('sender', 'receiver', 'timestamp', 'is_read', 'conversation_link')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('sender', 'receiver', 'conversation_link', 'timestamp', 'is_read')
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
    
    def content_short(self, obj):
        if obj.content and len(obj.content) > 50:
            return obj.content[:50] + '...'
        return obj.content
    content_short.short_description = 'Nội dung'
    
    def conversation_link(self, obj):
        if obj.conversation:
            url = reverse('admin:chat_conversation_change', args=[obj.conversation.id])
            return format_html('<a href="{}">{}</a>', url, f"Cuộc hội thoại #{obj.conversation.id}")
        return '-'
    conversation_link.short_description = 'Cuộc hội thoại'
    
    actions = ['mark_as_reviewed', 'hide_messages']
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(content_status='REVIEWED', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_as_reviewed.short_description = "Đánh dấu là đã kiểm duyệt"
    
    def hide_messages(self, request, queryset):
        queryset.update(content_status='HIDDEN', reviewed_by=request.user, reviewed_at=timezone.now())
    hide_messages.short_description = "Ẩn tin nhắn đã chọn"

@admin.register(MessageReport)
class MessageReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'reporter', 'reason', 'status', 'timestamp')
    list_filter = ('status', 'reason', 'timestamp')
    search_fields = ('reporter__username', 'message__content', 'description')
    ordering = ('-timestamp',)
    readonly_fields = ('message', 'reporter', 'timestamp', 'message_content')
    
    fieldsets = (
        ('Thông tin báo cáo', {
            'fields': ('message', 'message_content', 'reporter', 'reason', 'description', 'timestamp')
        }),
        ('Xử lý báo cáo', {
            'fields': ('status', 'handled_by', 'handled_at', 'action_taken')
        }),
    )
    
    def message_content(self, obj):
        if obj.message:
            return obj.message.content
        return '-'
    message_content.short_description = 'Nội dung tin nhắn'
    
    actions = ['mark_as_reviewed', 'mark_as_resolved', 'dismiss_reports']
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='REVIEWED', handled_by=request.user, handled_at=timezone.now())
    mark_as_reviewed.short_description = "Đánh dấu là đã xem xét"
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='RESOLVED', handled_by=request.user, handled_at=timezone.now())
    mark_as_resolved.short_description = "Đánh dấu là đã giải quyết"
    
    def dismiss_reports(self, request, queryset):
        queryset.update(status='DISMISSED', handled_by=request.user, handled_at=timezone.now())
    dismiss_reports.short_description = "Bác bỏ báo cáo"

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
    
    actions = ['deactivate_restrictions', 'activate_restrictions']
    
    def deactivate_restrictions(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_restrictions.short_description = "Huỷ hạn chế cho các tài khoản đã chọn"
    
    def activate_restrictions(self, request, queryset):
        queryset.update(is_active=True)
    activate_restrictions.short_description = "Kích hoạt hạn chế cho các tài khoản đã chọn"

# Import lớp User
from django.contrib.auth import get_user_model
User = get_user_model()