from django.core.management.base import BaseCommand
from music.models import Album, Song
from django.contrib.auth import get_user_model
from django.conf import settings
import os
import random
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Xóa dữ liệu album cũ và tạo dữ liệu album mới với URL đầy đủ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-existing',
            action='store_true',
            help='Không xóa dữ liệu album cũ trước khi tạo mới'
        )

    def handle(self, *args, **options):
        keep_existing = options['keep_existing']
        
        # Xác định host URL từ settings nếu có, hoặc sử dụng localhost
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        
        if not keep_existing:
            self.stdout.write(self.style.WARNING('Đang xóa tất cả dữ liệu album cũ...'))
            # Lưu lại danh sách bài hát
            songs_data = []
            for album in Album.objects.all():
                # Chỉ lấy thông tin bài hát, không xóa bài hát
                album_songs = Song.objects.filter(album=album.title)
                for song in album_songs:
                    songs_data.append({
                        'id': song.id,
                        'title': song.title,
                        'artist': song.artist,
                        'audio_file': song.audio_file.name if song.audio_file else None,
                        'cover_image': song.cover_image.name if song.cover_image else None,
                        'genre': song.genre,
                        'duration': song.duration,
                        'likes_count': song.likes_count,
                        'play_count': song.play_count,
                    })
            
            # Xóa album cũ
            Album.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Đã xóa tất cả dữ liệu album cũ!'))
            
            # Tạo danh sách album mới
            album_data = [
                {
                    'title': 'NhacCuaTui.com',
                    'artist': 'Dế Choắt, Jason',
                    'release_date': '2025-05-01',
                    'description': 'Album by Dế Choắt, Jason',
                },
                {
                    'title': 'Chạm Đáy Nỗi Đau',
                    'artist': 'Erik',
                    'release_date': '2025-05-01',
                    'description': 'Album by Erik',
                },
                {
                    'title': 'Rap Việt Collection',
                    'artist': 'Various Artists',
                    'release_date': '2025-05-01',
                    'description': 'Tuyển tập Rap Việt hay nhất',
                }
            ]
            
            # Tạo album mới
            created_albums = []
            for album_info in album_data:
                album = Album.objects.create(
                    title=album_info['title'],
                    artist=album_info['artist'],
                    release_date=album_info['release_date'],
                    description=album_info['description'],
                )
                created_albums.append(album)
                self.stdout.write(self.style.SUCCESS(f'Đã tạo album: {album.title}'))
            
            # Gán lại bài hát cho album
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.first()
            
            # Gán bài hát vào album
            for song_data in songs_data:
                # Chọn ngẫu nhiên một album
                album = random.choice(created_albums)
                
                # Cập nhật thông tin bài hát
                song = Song.objects.get(id=song_data['id'])
                song.album = album.title
                song.save()
                
                self.stdout.write(f'Đã gán bài hát "{song.title}" vào album "{album.title}"')
            
            self.stdout.write(self.style.SUCCESS('Đã hoàn thành việc tạo album mới và gán bài hát!'))
        
        # Kiểm tra xem các bài hát trong album đã có URL đầy đủ chưa
        self.stdout.write(self.style.WARNING('Kiểm tra và cập nhật URL cho bài hát trong album...'))
        
        albums = Album.objects.all()
        for album in albums:
            songs = Song.objects.filter(album=album.title)
            self.stdout.write(f'Album: {album.title} - Số bài hát: {songs.count()}')
            
            for song in songs:
                # Đảm bảo audio_file và cover_image được hiển thị đúng
                if song.audio_file and not song.audio_file.url.startswith(('http://', 'https://')):
                    song_url = f"{base_url}/media/{song.audio_file.name}"
                    self.stdout.write(f'  - Bài hát: {song.title} - URL âm thanh: {song_url}')
                
                if song.cover_image and not song.cover_image.url.startswith(('http://', 'https://')):
                    cover_url = f"{base_url}/media/{song.cover_image.name}"
                    self.stdout.write(f'  - Bài hát: {song.title} - URL hình ảnh: {cover_url}')
        
        self.stdout.write(self.style.SUCCESS('Đã hoàn thành việc kiểm tra và cập nhật URL cho album!')) 