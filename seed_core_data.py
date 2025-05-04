#!/usr/bin/env python
"""
Script để tạo dữ liệu cơ bản cho hệ thống:
- Người dùng
- Thể loại nhạc
- Nghệ sĩ
- Bài hát
- Album
- Playlist
"""

import os
import sys
import django
import random
from django.db.models import Count
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from music.models import Song, Genre, Artist, Album, Playlist
from django.utils import timezone

User = get_user_model()

def create_users(num_users=10):
    """Tạo người dùng"""
    print(f"Đang tạo {num_users} người dùng...")
    
    # Kiểm tra xem đã có admin chưa
    if not User.objects.filter(email='admin@example.com').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='Admin123!',
            first_name='Admin',
            last_name='User'
        )
        print("Đã tạo tài khoản admin")
    
    # Tạo người dùng thường
    first_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Võ', 'Đặng', 'Bùi', 'Đỗ']
    last_names = ['An', 'Bình', 'Cường', 'Dũng', 'Hà', 'Hải', 'Hùng', 'Lan', 'Long', 'Mai', 'Minh', 'Nam', 'Ngọc', 'Phong', 'Thảo', 'Trang', 'Tuấn', 'Việt']
    
    count = 0
    for i in range(num_users):
        # Tạo thông tin ngẫu nhiên
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"user{i+1}"
        email = f"user{i+1}@example.com"
        
        # Kiểm tra xem user đã tồn tại chưa
        if not User.objects.filter(email=email).exists():
            User.objects.create_user(
                username=username,
                email=email,
                password='Password123!',
                first_name=first_name,
                last_name=last_name,
                bio=f"Xin chào, tôi là {first_name} {last_name}. Tôi yêu thích âm nhạc và muốn chia sẻ với mọi người."
            )
            count += 1
    
    print(f"Đã tạo {count} người dùng mới")

def create_genres():
    """Tạo các thể loại nhạc"""
    print("Đang tạo thể loại nhạc...")
    
    genres = [
        'Pop', 'Rock', 'Hip Hop', 'R&B', 'Electronic', 'Jazz', 'Classical', 
        'Country', 'Folk', 'Blues', 'Metal', 'Reggae', 'Indie', 'Dance', 
        'Funk', 'Soul', 'Punk', 'Disco', 'Alternative', 'K-Pop', 'V-Pop', 
        'Latin', 'Acoustic', 'Ambient', 'Instrumental'
    ]
    
    count = 0
    for genre_name in genres:
        genre, created = Genre.objects.get_or_create(name=genre_name)
        if created:
            count += 1
    
    print(f"Đã tạo {count} thể loại nhạc mới")

def create_artists(num_artists=15):
    """Tạo nghệ sĩ"""
    print(f"Đang tạo {num_artists} nghệ sĩ...")
    
    vietnamese_artists = [
        'Sơn Tùng M-TP', 'Hồ Ngọc Hà', 'Đen Vâu', 'Mỹ Tâm', 'Bích Phương',
        'Binz', 'Vũ', 'Min', 'Hoàng Thùy Linh', 'Tóc Tiên', 
        'Noo Phước Thịnh', 'Jack', 'Bùi Anh Tuấn', 'Chi Pu', 'Đức Phúc'
    ]
    
    international_artists = [
        'Ed Sheeran', 'Taylor Swift', 'BTS', 'Ariana Grande', 'The Weeknd',
        'Billie Eilish', 'Justin Bieber', 'Drake', 'Adele', 'Coldplay',
        'Beyoncé', 'Lady Gaga', 'Bruno Mars', 'Post Malone', 'Dua Lipa'
    ]
    
    count = 0
    # Tạo nghệ sĩ Việt Nam
    for artist_name in vietnamese_artists[:num_artists//2]:
        artist, created = Artist.objects.get_or_create(
            name=artist_name,
            defaults={
                'bio': f"{artist_name} là nghệ sĩ nổi tiếng của Việt Nam.",
                'country': 'Vietnam'
            }
        )
        if created:
            count += 1
    
    # Tạo nghệ sĩ quốc tế
    for artist_name in international_artists[:(num_artists - num_artists//2)]:
        artist, created = Artist.objects.get_or_create(
            name=artist_name,
            defaults={
                'bio': f"{artist_name} là nghệ sĩ nổi tiếng trên thế giới.",
                'country': 'International'
            }
        )
        if created:
            count += 1
    
    print(f"Đã tạo {count} nghệ sĩ mới")

def create_songs(num_songs=50):
    """Tạo bài hát"""
    print(f"Đang tạo {num_songs} bài hát...")
    
    # Lấy dữ liệu cần thiết
    artists = Artist.objects.all()
    genres = Genre.objects.all()
    
    if not artists.exists():
        print("Không có nghệ sĩ để tạo bài hát")
        return
        
    if not genres.exists():
        print("Không có thể loại để tạo bài hát")
        return
    
    # Tên bài hát tiếng Việt
    vietnamese_song_names = [
        'Có Chắc Yêu Là Đây', 'Chúng Ta Của Hiện Tại', 'Sáng Mắt Chưa', 
        'Đừng Chờ Anh Nữa', 'Hãy Trao Cho Anh', 'Tình Bạn Diệu Kỳ', 
        'Hoa Hải Đường', 'Waiting For You', 'Em Bỏ Hút Thuốc Chưa', 
        'Muộn Rồi Mà Sao Còn', 'Đi Về Nhà', 'Trốn Tìm', 'Vì Mẹ Anh Bắt Chia Tay',
        'Răng Khôn', 'Thích Em Hơi Nhiều', 'Lối Nhỏ', 'Phải Chăng Em Đã Yêu',
        'Rồi Tới Luôn', 'Sài Gòn Đau Lòng Quá', 'Tại Vì Sao', 'Có Hẹn Với Thanh Xuân'
    ]
    
    # Tên bài hát tiếng Anh
    english_song_names = [
        'Shape of You', 'Blinding Lights', 'Dance Monkey', 'Bad Guy', 'Stay',
        'Levitating', 'Heat Waves', 'Watermelon Sugar', 'Save Your Tears',
        'Peaches', 'Dynamite', 'Butter', 'Circles', 'Don\'t Start Now',
        'Positions', 'Good 4 U', 'Beggin\'', 'Montero', 'Industry Baby',
        'Easy On Me', 'Cold Heart', 'Stay With Me', 'Perfect', 'All Of Me'
    ]
    
    count = 0
    for i in range(num_songs):
        # Chọn nghệ sĩ và thể loại ngẫu nhiên
        artist = random.choice(artists)
        genre = random.choice(genres)
        
        # Chọn tên bài hát dựa trên quốc gia của nghệ sĩ
        if artist.country == 'Vietnam':
            if vietnamese_song_names:
                title = vietnamese_song_names.pop(0) if len(vietnamese_song_names) > 0 else f"Bài hát Việt {i+1}"
            else:
                title = f"Bài hát Việt {i+1}"
        else:
            if english_song_names:
                title = english_song_names.pop(0) if len(english_song_names) > 0 else f"English Song {i+1}"
            else:
                title = f"English Song {i+1}"
        
        # Tạo bài hát
        song, created = Song.objects.get_or_create(
            title=title,
            artist=artist,
            defaults={
                'genre': genre,
                'duration': random.randint(180, 300),  # 3-5 phút
                'release_date': timezone.now() - timedelta(days=random.randint(1, 365*3)),  # 1 ngày - 3 năm
                'lyrics': f"Đây là lời bài hát cho {title}...\n\nVerse 1:\nLorem ipsum dolor sit amet...\n\nChorus:\nLorem ipsum dolor sit amet...",
                'play_count': random.randint(100, 10000)
            }
        )
        
        if created:
            count += 1
    
    print(f"Đã tạo {count} bài hát mới")

def create_playlists(num_playlists=20):
    """Tạo playlist"""
    print(f"Đang tạo {num_playlists} playlist...")
    
    # Lấy dữ liệu cần thiết
    users = User.objects.all()
    songs = Song.objects.all()
    
    if not users.exists():
        print("Không có người dùng để tạo playlist")
        return
        
    if not songs.exists():
        print("Không có bài hát để tạo playlist")
        return
    
    # Tên playlist tiếng Việt
    playlist_names = [
        'Nhạc Chill Cuối Tuần', 'Những Bài Hát Hay Nhất', 'Top Hits Việt Nam',
        'Nhạc Trẻ Hay Nhất', 'Acoustic Chill', 'Love Songs', 'Workout Vibes',
        'Nhạc Buồn Tâm Trạng', 'K-Pop Hits', 'Throwbacks', 'Driving Music',
        'Study Focus', 'Party Mix', 'Relax & Unwind', 'Morning Coffee',
        'Fitness Motivation', 'Rainy Day', 'Happy Vibes', 'Summer Hits',
        'Gaming Mix', 'Deep Focus', 'Nhạc US-UK', 'Nhạc Hoa Hay Nhất'
    ]
    
    count = 0
    for i in range(num_playlists):
        # Chọn người dùng và tên playlist ngẫu nhiên
        user = random.choice(users)
        
        if playlist_names:
            name = playlist_names.pop(0) if len(playlist_names) > 0 else f"Playlist {i+1}"
        else:
            name = f"Playlist {i+1}"
        
        # Tạo playlist
        playlist, created = Playlist.objects.get_or_create(
            name=name,
            user=user,
            defaults={
                'description': f"Đây là playlist {name} của {user.username}",
                'is_public': random.choice([True, True, False]),  # 2/3 là công khai
                'created_at': timezone.now() - timedelta(days=random.randint(1, 180))  # 1 ngày - 6 tháng
            }
        )
        
        if created:
            # Thêm bài hát vào playlist
            num_songs = random.randint(5, 20)
            playlist_songs = random.sample(list(songs), min(num_songs, songs.count()))
            playlist.songs.set(playlist_songs)
            
            count += 1
    
    print(f"Đã tạo {count} playlist mới")

def run_all():
    """Chạy tất cả các hàm tạo dữ liệu"""
    print("Bắt đầu tạo dữ liệu cơ bản cho hệ thống...")
    
    create_users()
    create_genres()
    create_artists()
    create_songs()
    create_playlists()
    
    print("Hoàn thành tạo dữ liệu cơ bản!")

if __name__ == "__main__":
    run_all() 