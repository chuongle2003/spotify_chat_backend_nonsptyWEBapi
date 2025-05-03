from django.db import models
from django.conf import settings

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

    class Meta:
        db_table = 'playlists'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} by {self.user.username}"

    def can_access(self, user):
        if self.is_public:
            return True
        return user == self.user

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
        return f"Recommendation: {self.song.title} for {self.user.username}"