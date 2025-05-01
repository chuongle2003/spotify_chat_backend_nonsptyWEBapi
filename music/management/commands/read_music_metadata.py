import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from django.core.management.base import BaseCommand
from music.models import Genre, Album, Song
from django.contrib.auth import get_user_model
from django.core.files import File as DjangoFile
from datetime import datetime
from io import BytesIO

User = get_user_model()

class Command(BaseCommand):
    help = 'Read music metadata from files and create database entries'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to read music metadata...'))
        
        # Lấy admin user
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Đường dẫn đến thư mục music_sample
        base_dir = 'music_sample'
        
        # Duyệt qua các thư mục thể loại
        for genre_dir in os.listdir(base_dir):
            genre_path = os.path.join(base_dir, genre_dir)
            if not os.path.isdir(genre_path):
                continue
                
            # Tạo hoặc lấy thể loại
            genre_name = genre_dir.replace('_', ' ').title()
            genre, created = Genre.objects.get_or_create(
                name=genre_name,
                defaults={'description': f'Music in the {genre_name} genre.'}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created genre: {genre_name}'))
            
            # Duyệt qua các file trong thư mục thể loại
            for filename in os.listdir(genre_path):
                if not filename.lower().endswith('.mp3'):
                    continue
                    
                file_path = os.path.join(genre_path, filename)
                
                try:
                    # Đọc metadata từ file MP3
                    audio = MP3(file_path)
                    
                    # Lấy thông tin cơ bản từ tên file nếu không có metadata
                    title = filename.split('.')[0]
                    artist = 'Unknown Artist'
                    album_name = 'Unknown Album'
                    
                    # Thử đọc ID3 tags nếu có
                    try:
                        tags = ID3(file_path)
                        if 'TIT2' in tags:  # Title
                            title = str(tags['TIT2'])
                        if 'TPE1' in tags:  # Artist
                            artist = str(tags['TPE1'])
                        if 'TALB' in tags:  # Album
                            album_name = str(tags['TALB'])
                    except:
                        pass
                    
                    # Lấy thời lượng
                    duration = int(audio.info.length)
                    
                    # Tạo hoặc lấy album
                    album_obj, created = Album.objects.get_or_create(
                        title=album_name,
                        artist=artist,
                        defaults={
                            'release_date': datetime.now().date(),
                            'description': f'Album by {artist}'
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created album: {album_name}'))
                    
                    # Tạo bài hát
                    song, created = Song.objects.get_or_create(
                        title=title,
                        artist=artist,
                        album=album_name,
                        defaults={
                            'duration': duration,
                            'genre': genre_name,
                            'uploaded_by': admin,
                            'likes_count': 0,
                            'play_count': 0,
                            'lyrics': 'Lyrics not available'
                        }
                    )
                    
                    if created:
                        # Lưu file âm thanh
                        with open(file_path, 'rb') as f:
                            song.audio_file.save(filename, DjangoFile(f), save=True)
                            
                        # Lưu ảnh bìa nếu có
                        try:
                            if tags and 'APIC:' in tags:
                                cover = tags['APIC:'].data
                                song.cover_image.save(f'{title}.jpg', DjangoFile(BytesIO(cover)), save=True)
                        except:
                            pass
                            
                        self.stdout.write(self.style.SUCCESS(f'Created song: {title}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Song already exists: {title}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing {filename}: {str(e)}'))
                    
        self.stdout.write(self.style.SUCCESS('Finished reading music metadata!')) 