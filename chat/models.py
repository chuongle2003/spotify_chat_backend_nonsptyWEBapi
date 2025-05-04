from django.db import models
from django.conf import settings
from music.models import Song, Playlist

User = settings.AUTH_USER_MODEL

class Message(models.Model):
    MESSAGE_TYPES = (
        ('TEXT', 'Text Message'),
        ('SONG', 'Song Share'),
        ('PLAYLIST', 'Playlist Share'),
        ('IMAGE', 'Image Message'),
        ('VOICE', 'Voice Message'),
        ('FILE', 'File Attachment'),
    )

    CONTENT_STATUS = (
        ('NORMAL', 'Normal Content'),
        ('FLAGGED', 'Flagged by System'),
        ('REPORTED', 'Reported by User'),
        ('REVIEWED', 'Reviewed by Admin'),
        ('HIDDEN', 'Hidden by Admin'),
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_received_messages')
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='TEXT')
    
    # File attachments
    attachment = models.FileField(upload_to='message_attachments/%Y/%m/%d/', null=True, blank=True)
    image = models.ImageField(upload_to='message_images/%Y/%m/%d/', null=True, blank=True)
    voice_note = models.FileField(upload_to='voice_notes/%Y/%m/%d/', null=True, blank=True)
    
    # Music sharing - thêm related_name để tránh xung đột
    shared_song = models.ForeignKey('music.Song', on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='chat_messages')
    shared_playlist = models.ForeignKey('music.Playlist', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='chat_messages')
    
    # Thêm trường cho kiểm duyệt
    content_status = models.CharField(max_length=10, choices=CONTENT_STATUS, default='NORMAL')
    review_note = models.TextField(blank=True, help_text="Ghi chú của admin khi kiểm duyệt")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='reviewed_messages')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_messages'

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"

    def clean(self):
        from django.core.exceptions import ValidationError
        attachments = [
            bool(self.attachment),
            bool(self.image),
            bool(self.voice_note),
            bool(self.shared_song),
            bool(self.shared_playlist)
        ]
        if sum(attachments) > 1:
            raise ValidationError('Chỉ được phép đính kèm một loại nội dung')

    def save(self, *args, **kwargs):
        self.clean()
        if self.shared_song:
            self.message_type = 'SONG'
        elif self.shared_playlist:
            self.message_type = 'PLAYLIST'
        elif self.image:
            self.message_type = 'IMAGE'
        elif self.voice_note:
            self.message_type = 'VOICE'
        elif self.attachment:
            self.message_type = 'FILE'
        super().save(*args, **kwargs)

class MessageReport(models.Model):
    REPORT_REASONS = (
        ('INAPPROPRIATE', 'Nội dung không phù hợp'),
        ('SPAM', 'Tin nhắn spam'),
        ('HARASSMENT', 'Quấy rối'),
        ('HATE_SPEECH', 'Phát ngôn thù ghét'),
        ('OTHER', 'Lý do khác'),
    )
    
    REPORT_STATUS = (
        ('PENDING', 'Đang chờ xử lý'),
        ('REVIEWED', 'Đã xem xét'),
        ('RESOLVED', 'Đã giải quyết'),
        ('DISMISSED', 'Bác bỏ'),
    )
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_messages')
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=REPORT_STATUS, default='PENDING')
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='handled_reports')
    handled_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.TextField(blank=True, help_text="Hành động đã thực hiện đối với báo cáo này")
    
    class Meta:
        db_table = 'chat_message_reports'
        
    def __str__(self):
        return f"Report on message {self.message.id} by {self.reporter.username}"

class ChatRestriction(models.Model):
    RESTRICTION_TYPES = (
        ('TEMPORARY', 'Hạn chế tạm thời'),
        ('PERMANENT', 'Hạn chế vĩnh viễn'),
        ('WARNING', 'Cảnh báo'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_restrictions')
    restriction_type = models.CharField(max_length=10, choices=RESTRICTION_TYPES)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                 null=True, related_name='created_restrictions')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chat_restrictions'
        
    def __str__(self):
        return f"{self.restriction_type} restriction for {self.user.username}"
        
    @property
    def is_expired(self):
        """Kiểm tra xem hạn chế đã hết hạn chưa"""
        if self.restriction_type == 'PERMANENT':
            return False
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at