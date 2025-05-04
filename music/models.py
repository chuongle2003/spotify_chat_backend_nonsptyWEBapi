from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    album = models.CharField(max_length=200, blank=True)
    duration = models.IntegerField()  # seconds
    audio_file = models.FileField(upload_to='songs/%Y/%m/%d/')
    cover_image = models.ImageField(upload_to='covers/%Y/%m/%d/', null=True, blank=True)
    genre = models.CharField(max_length=100, blank=True)
    likes_count = models.IntegerField(default=0)
    play_count = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    lyrics = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'songs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist}"

class Playlist(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    songs = models.ManyToManyField(Song, related_name='playlists')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    cover_image = models.ImageField(upload_to='playlist_covers/', null=True, blank=True)
    followers = models.ManyToManyField(User, related_name='followed_playlists', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Thêm trường cho Collaborative Playlist
    is_collaborative = models.BooleanField(default=False, help_text="Playlist có thể được chỉnh sửa bởi nhiều người cộng tác")
    collaborators = models.ManyToManyField(User, through='CollaboratorRole', related_name='collaborative_playlists', through_fields=('playlist', 'user'))

    class Meta:
        db_table = 'playlists'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} by {self.user.username}"

    def can_access(self, user):
        if self.is_public:
            return True
        return user == self.user or (self.is_collaborative and user in self.collaborators.all())
    
    def can_edit(self, user):
        """Kiểm tra xem người dùng có quyền chỉnh sửa playlist không"""
        # Chủ sở hữu luôn có quyền chỉnh sửa
        if user == self.user:
            return True
        
        # Admin luôn có quyền chỉnh sửa
        if user.is_admin:
            return True
        
        # Kiểm tra xem người dùng có phải là người cộng tác có quyền chỉnh sửa không
        if self.is_collaborative:
            try:
                role = CollaboratorRole.objects.get(playlist=self, user=user)
                return role.can_edit
            except CollaboratorRole.DoesNotExist:
                return False
                
        return False

class CollaboratorRole(models.Model):
    """Model để lưu trữ vai trò của người cộng tác trong playlist"""
    ROLE_CHOICES = (
        ('EDITOR', 'Người chỉnh sửa'),
        ('VIEWER', 'Người xem'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlist_roles')
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='VIEWER')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_collaborators')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'playlist_collaborator_roles'
        unique_together = ('user', 'playlist')
        
    def __str__(self):
        return f"{self.user.username} as {self.role} on {self.playlist.name}"
        
    @property
    def can_edit(self):
        """Kiểm tra xem vai trò có quyền chỉnh sửa không"""
        return self.role == 'EDITOR'

class PlaylistEditHistory(models.Model):
    """Lưu lịch sử chỉnh sửa của playlist"""
    ACTION_TYPES = (
        ('CREATE', 'Tạo mới'),
        ('UPDATE_INFO', 'Cập nhật thông tin'),
        ('ADD_SONG', 'Thêm bài hát'),
        ('REMOVE_SONG', 'Xóa bài hát'),
        ('ADD_COLLABORATOR', 'Thêm cộng tác viên'),
        ('REMOVE_COLLABORATOR', 'Xóa cộng tác viên'),
        ('CHANGE_ROLE', 'Thay đổi vai trò'),
        ('RESTORE', 'Khôi phục'),
    )
    
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='edit_history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='playlist_edits')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, help_text="Chi tiết về hành động chỉnh sửa")
    
    # Tham chiếu đến đối tượng liên quan (nếu có)
    related_song = models.ForeignKey(Song, on_delete=models.SET_NULL, null=True, blank=True, related_name='playlist_history')
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='playlist_history_mentions')
    
    class Meta:
        db_table = 'playlist_edit_history'
        ordering = ['-timestamp']
        
    def __str__(self):
        user_name = self.user.username if self.user else "Unknown User"
        return f"{user_name} {self.get_action_display()} on {self.playlist.name} at {self.timestamp}"
        
    @classmethod
    def log_action(cls, playlist, user, action, details=None, related_song=None, related_user=None):
        """Helper method để tạo bản ghi lịch sử mới"""
        if details is None:
            details = {}
            
        return cls.objects.create(
            playlist=playlist,
            user=user,
            action=action,
            details=details,
            related_song=related_song,
            related_user=related_user
        )

class Message(models.Model):
    MESSAGE_TYPES = (
        ('TEXT', 'Text Message'),
        ('SONG', 'Song Share'),
        ('PLAYLIST', 'Playlist Share'),
        ('IMAGE', 'Image Message'),
        ('VOICE', 'Voice Message'),
        ('FILE', 'File Attachment'),
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='music_sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='music_received_messages')
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='TEXT')
    
    # File attachments
    attachment = models.FileField(upload_to='message_attachments/%Y/%m/%d/', null=True, blank=True)
    image = models.ImageField(upload_to='message_images/%Y/%m/%d/', null=True, blank=True)
    voice_note = models.FileField(upload_to='voice_notes/%Y/%m/%d/', null=True, blank=True)
    
    # Music sharing - thêm related_name để tránh xung đột
    shared_song = models.ForeignKey(Song, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='music_messages')
    shared_playlist = models.ForeignKey(Playlist, on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='music_messages')

    class Meta:
        db_table = 'music_messages'

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

class UserActivity(models.Model):
    ACTIVITY_TYPES = (
        ('PLAY', 'Played Song'),
        ('LIKE', 'Liked Song'),
        ('FOLLOW', 'Followed User'),
        ('CREATE_PLAYLIST', 'Created Playlist'),
        ('ADD_TO_PLAYLIST', 'Added Song to Playlist'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, null=True, blank=True)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, null=True, blank=True)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='targeted_activities')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_activities'
        ordering = ['-timestamp']

class SongPlayHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='play_history')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='play_history')
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'song_play_history'
        ordering = ['-played_at']

class Album(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    release_date = models.DateField()
    cover_image = models.ImageField(upload_to='album_covers/%Y/%m/%d/', null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'albums'
        ordering = ['-release_date']

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='genre_images/', null=True, blank=True)
    
    class Meta:
        db_table = 'genres'

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']

class Rating(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ratings'
        unique_together = ['user', 'song']  # Một user chỉ đánh giá một bài hát một lần

class LyricLine(models.Model):
    """Model lưu trữ từng dòng lời bài hát đồng bộ với thời gian"""
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='lyric_lines')
    timestamp = models.FloatField(help_text="Thời điểm hiển thị lời (tính bằng giây)")
    text = models.TextField()
    
    class Meta:
        db_table = 'lyric_lines'
        ordering = ['timestamp']
        
    def __str__(self):
        return f"[{self.format_timestamp()}] {self.text[:30]}"
    
    def format_timestamp(self):
        """Định dạng timestamp thành [mm:ss.xx]"""
        minutes = int(self.timestamp // 60)
        seconds = self.timestamp % 60
        return f"{minutes:02d}:{seconds:05.2f}"

class Artist(models.Model):
    """Model cho nghệ sĩ"""
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='artist_images/', null=True, blank=True)
    
    class Meta:
        db_table = 'artists'
        
    def __str__(self):
        return self.name

class Queue(models.Model):
    """Model lưu trữ hàng đợi phát nhạc của người dùng"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='queue')
    songs = models.ManyToManyField(Song, through='QueueItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'queues'
        
    def __str__(self):
        return f"Queue for {self.user.username}"

class QueueItem(models.Model):
    """Model lưu trữ từng bài hát trong hàng đợi"""
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'queue_items'
        ordering = ['position']
        unique_together = ['queue', 'position']
        
    def __str__(self):
        return f"{self.position}. {self.song.title} in {self.queue}"

class UserStatus(models.Model):
    """Model lưu trạng thái hiện tại của người dùng"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='music_status')
    currently_playing = models.ForeignKey(Song, on_delete=models.SET_NULL, null=True, blank=True)
    status_text = models.CharField(max_length=255, blank=True)
    is_listening = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_statuses'
        
    def __str__(self):
        return f"Status for {self.user.username}"

class UserRecommendation(models.Model):
    """Model lưu trữ các đề xuất bài hát cho người dùng"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='recommended_to')
    score = models.FloatField(default=0.0)  # Điểm đề xuất để xếp hạng
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_recommendations'
        ordering = ['-score', '-created_at']
        unique_together = ['user', 'song']  # Mỗi bài hát chỉ được đề xuất một lần cho một người dùng
        
    def __str__(self):
        return f"{self.user.username} - {self.song.title} ({self.score})"

class OfflineDownload(models.Model):
    """Model lưu trữ thông tin các bài hát đã được tải xuống để nghe offline"""
    STATUS_CHOICES = (
        ('PENDING', 'Đang chờ tải xuống'),
        ('DOWNLOADING', 'Đang tải xuống'),
        ('COMPLETED', 'Đã tải xuống hoàn tất'),
        ('FAILED', 'Tải xuống thất bại'),
        ('EXPIRED', 'Đã hết hạn')
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offline_downloads')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='offline_downloads')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    progress = models.IntegerField(default=0)  # Tiến độ tải xuống (0-100)
    local_path = models.CharField(max_length=500, blank=True, null=True)  # Đường dẫn lưu trữ cục bộ
    download_time = models.DateTimeField(auto_now_add=True)  # Thời điểm tải xuống
    expiry_time = models.DateTimeField(null=True, blank=True)  # Thời điểm hết hạn (nếu có)
    is_active = models.BooleanField(default=True)  # Trạng thái còn khả dụng hay không
    
    class Meta:
        db_table = 'offline_downloads'
        ordering = ['-download_time']
        unique_together = ['user', 'song']  # Mỗi người dùng chỉ tải một bài hát một lần

    def __str__(self):
        return f"{self.user.username} - {self.song.title} ({self.get_status_display()})"
    
    def is_available(self):
        """Kiểm tra xem bài hát có khả dụng cho chế độ offline không"""
        if not self.is_active:
            return False
        
        if self.status != 'COMPLETED':
            return False
            
        if self.expiry_time and self.expiry_time < timezone.now():
            self.status = 'EXPIRED'
            self.is_active = False
            self.save()
            return False
            
        return True