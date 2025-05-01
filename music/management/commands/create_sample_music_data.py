from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from music.models import Genre, Album, Song, Playlist, SongPlayHistory, Comment, Rating
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import timedelta
import random
import os
import requests
from io import BytesIO
from PIL import Image

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample music data for the music app'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to create sample music data...'))
        
        # Tạo admin user nếu chưa tồn tại
        if not User.objects.filter(is_superuser=True).exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            # Lưu ý: is_superuser và is_staff đã được set trong create_superuser
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        else:
            admin = User.objects.filter(is_superuser=True).first()
            
        # Tạo một số người dùng thông thường
        users = []
        usernames = ['user1', 'user2', 'user3', 'user4', 'user5']
        for i, username in enumerate(usernames, 1):
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='password123'
                )
                users.append(user)
                self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            else:
                users.append(User.objects.get(username=username))
                
        # Tạo thể loại
        genres = ['Pop', 'Rock', 'Jazz', 'Electronic', 'Classical', 'Hip Hop', 'R&B', 'Country', 'Folk', 'Latin']
        genre_objects = []
        
        for genre_name in genres:
            genre, created = Genre.objects.get_or_create(
                name=genre_name,
                defaults={'description': f'Music in the {genre_name} genre.'}
            )
            genre_objects.append(genre)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created genre: {genre_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Genre already exists: {genre_name}'))
        
        # Tạo album
        albums_data = [
            {'title': 'Summer Vibes', 'artist': 'The Sunshine Band', 'genre': 'Pop'},
            {'title': 'Rock Revolution', 'artist': 'Thunder Strike', 'genre': 'Rock'},
            {'title': 'Smooth Jazz Collection', 'artist': 'Night City Quartet', 'genre': 'Jazz'},
            {'title': 'Electronic Dreams', 'artist': 'Digital Pulse', 'genre': 'Electronic'},
            {'title': 'Classical Masterpieces', 'artist': 'Symphony Orchestra', 'genre': 'Classical'},
            {'title': 'Hip Hop Essentials', 'artist': 'Urban Poets', 'genre': 'Hip Hop'},
            {'title': 'Soul Feelings', 'artist': 'The Emotions', 'genre': 'R&B'},
            {'title': 'Country Roads', 'artist': 'Western Stars', 'genre': 'Country'},
            {'title': 'Folk Traditions', 'artist': 'Acoustic Storytellers', 'genre': 'Folk'},
            {'title': 'Latin Rhythms', 'artist': 'Salsa Kings', 'genre': 'Latin'},
        ]
        
        album_objects = []
        for album_data in albums_data:
            # Tìm thể loại tương ứng
            genre = next((g for g in genre_objects if g.name == album_data['genre']), None)
            
            # Tạo album mới hoặc lấy album đã tồn tại
            album, created = Album.objects.get_or_create(
                title=album_data['title'],
                artist=album_data['artist'],
                defaults={
                    'release_date': timezone.now().date() - timedelta(days=random.randint(0, 365)),
                    'description': f"A collection of {album_data['genre']} songs by {album_data['artist']}."
                }
            )
            
            album_objects.append(album)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created album: {album_data['title']}"))
                
                # Tạo ảnh bìa dummy cho album
                try:
                    # Sử dụng placekitten.com để lấy ảnh ngẫu nhiên
                    img_size = 500
                    response = requests.get(f'https://placekitten.com/{img_size}/{img_size}')
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        img_io = BytesIO()
                        img.save(img_io, format='JPEG')
                        img_content = ContentFile(img_io.getvalue())
                        album.cover_image.save(f"{album_data['title'].replace(' ', '_')}.jpg", img_content, save=True)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Failed to create album cover: {str(e)}"))
            else:
                self.stdout.write(self.style.WARNING(f"Album already exists: {album_data['title']}"))
        
        # Tạo bài hát
        for album in album_objects:
            # Tìm thể loại tương ứng từ thông tin album
            album_genre = next((g for g in genre_objects if g.name in album.description), genre_objects[0])
            
            # Tạo nhiều bài hát cho mỗi album
            for i in range(1, 11):  # 10 bài hát mỗi album
                song_title = f"Track {i} - {album.title}"
                
                # Kiểm tra xem bài hát đã tồn tại chưa
                if not Song.objects.filter(title=song_title, artist=album.artist).exists():
                    # Tạo bài hát mới
                    song = Song(
                        title=song_title,
                        artist=album.artist,
                        album=album.title,
                        duration=random.randint(180, 300),  # 3-5 phút
                        genre=album_genre.name,
                        uploaded_by=admin,
                        likes_count=random.randint(0, 100),
                        play_count=random.randint(50, 1000),
                        lyrics=f"This is a sample lyric for {song_title}.\nLine 2 of the lyrics.\nLine 3 of the lyrics."
                    )
                    
                    # Tạo file âm thanh dummy (không có nội dung thực)
                    dummy_audio = ContentFile(b"dummy audio content")
                    song.audio_file.save(f"{song_title.replace(' ', '_')}.mp3", dummy_audio, save=False)
                    
                    # Sử dụng ảnh bìa album cho song
                    if album.cover_image:
                        song.cover_image = album.cover_image
                    
                    song.save()
                    self.stdout.write(self.style.SUCCESS(f'Created song: {song_title}'))
                    
                    # Tạo lượt nghe ngẫu nhiên
                    for _ in range(random.randint(10, 50)):
                        random_user = random.choice(users + [admin])
                        days_ago = random.randint(0, 30)
                        SongPlayHistory.objects.create(
                            user=random_user,
                            song=song,
                            played_at=timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
                        )
                    
                    # Tạo bình luận ngẫu nhiên
                    comments = [
                        "Great song!",
                        "Love this track!",
                        "This is my favorite!",
                        "Amazing melody!",
                        "Nice beat!"
                    ]
                    
                    for _ in range(random.randint(0, 5)):
                        random_user = random.choice(users)
                        Comment.objects.create(
                            user=random_user,
                            song=song,
                            content=random.choice(comments),
                            created_at=timezone.now() - timedelta(days=random.randint(0, 30))
                        )
                    
                    # Tạo đánh giá ngẫu nhiên
                    for user in random.sample(users, random.randint(0, len(users))):
                        Rating.objects.create(
                            user=user,
                            song=song,
                            rating=random.randint(3, 5)  # Đánh giá từ 3-5 sao
                        )
                else:
                    self.stdout.write(self.style.WARNING(f'Song already exists: {song_title}'))
        
        # Tạo playlist
        playlist_names = [
            'Top Hits 2023',
            'Relaxing Jazz',
            'Workout Motivation',
            'Study Music',
            'Party Anthems',
            'Road Trip Mix',
            'Chill Vibes',
            'Morning Coffee',
            'Evening Relaxation',
            'Weekend Fun'
        ]
        
        for i, name in enumerate(playlist_names):
            # Lấy người dùng tạo playlist (luân phiên giữa admin và người dùng thường)
            creator = admin if i % 2 == 0 else random.choice(users)
            
            # Kiểm tra xem playlist đã tồn tại chưa
            if not Playlist.objects.filter(name=name, user=creator).exists():
                # Tạo playlist mới
                playlist = Playlist.objects.create(
                    name=name,
                    user=creator,
                    description=f"A collection of songs for {name.lower()}",
                    is_public=True,
                    created_at=timezone.now() - timedelta(days=random.randint(0, 60))
                )
                
                # Thêm bài hát vào playlist
                songs = list(Song.objects.all())
                random.shuffle(songs)
                song_count = min(len(songs), random.randint(5, 15))
                
                for j in range(song_count):
                    playlist.songs.add(songs[j])
                
                # Thêm người theo dõi
                for user in random.sample(users, random.randint(0, len(users))):
                    if user != creator:
                        playlist.followers.add(user)
                
                # Thêm ảnh bìa
                try:
                    img_size = 400
                    response = requests.get(f'https://placekitten.com/{img_size}/{img_size}')
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        img_io = BytesIO()
                        img.save(img_io, format='JPEG')
                        img_content = ContentFile(img_io.getvalue())
                        playlist.cover_image.save(f"{name.replace(' ', '_')}.jpg", img_content, save=True)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Failed to create playlist cover: {str(e)}"))
                
                self.stdout.write(self.style.SUCCESS(f'Created playlist: {name} with {song_count} songs'))
            else:
                self.stdout.write(self.style.WARNING(f'Playlist already exists: {name}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample music data!')) 