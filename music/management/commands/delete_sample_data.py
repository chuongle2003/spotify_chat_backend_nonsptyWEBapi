from django.core.management.base import BaseCommand
from music.models import Genre, Album, Song, Playlist, SongPlayHistory, Comment, Rating
from django.contrib.auth import get_user_model
import os
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Delete all sample music data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting to delete sample music data...'))
        
        # Xóa các bản ghi liên quan
        SongPlayHistory.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all song play histories'))
        
        Comment.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all comments'))
        
        Rating.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all ratings'))
        
        # Xóa các bài hát và file media
        songs = Song.objects.all()
        for song in songs:
            # Xóa file âm thanh
            if song.audio_file:
                file_path = os.path.join(settings.MEDIA_ROOT, song.audio_file.name)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Xóa ảnh bìa
            if song.cover_image:
                file_path = os.path.join(settings.MEDIA_ROOT, song.cover_image.name)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        songs.delete()
        self.stdout.write(self.style.SUCCESS('Deleted all songs and their media files'))
        
        # Xóa các album
        albums = Album.objects.all()
        for album in albums:
            # Xóa ảnh bìa album
            if album.cover_image:
                file_path = os.path.join(settings.MEDIA_ROOT, album.cover_image.name)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        albums.delete()
        self.stdout.write(self.style.SUCCESS('Deleted all albums and their cover images'))
        
        # Xóa các playlist
        playlists = Playlist.objects.all()
        for playlist in playlists:
            # Xóa ảnh bìa playlist
            if playlist.cover_image:
                file_path = os.path.join(settings.MEDIA_ROOT, playlist.cover_image.name)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        playlists.delete()
        self.stdout.write(self.style.SUCCESS('Deleted all playlists and their cover images'))
        
        # Xóa các thể loại
        Genre.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all genres'))
        
        # Xóa các user mẫu (trừ admin)
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('Deleted all sample users'))
        
        self.stdout.write(self.style.SUCCESS('Successfully deleted all sample music data!')) 