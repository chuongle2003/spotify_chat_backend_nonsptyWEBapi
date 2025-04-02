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