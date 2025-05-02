# Lưu file này với tên generate_trending_data.py
import os
import django
import random
from datetime import datetime, timedelta

# Thiết lập Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_chat.settings')
django.setup()

from django.utils import timezone
from music.models import Song, SongPlayHistory
from django.contrib.auth import get_user_model
from utils.pylance_helpers import safe_get_related_field

User = get_user_model()

def generate_trending_data():
    print("Bắt đầu tạo dữ liệu trending giả lập...")
    
    # Lấy tất cả users và songs
    users = list(User.objects.all())
    all_songs = list(Song.objects.all())
    
    if not users or not all_songs:
        print("Không có đủ dữ liệu người dùng hoặc bài hát. Hãy tạo dữ liệu cơ bản trước.")
        return
    
    # Chọn một số bài hát để làm trending (khoảng 5-8 bài)
    num_trending = min(random.randint(5, 8), len(all_songs))
    trending_songs = random.sample(all_songs, num_trending)
    
    # Chọn một số bài hát để làm "rising" (khoảng 3-5 bài) - mới nổi gần đây
    num_rising = min(random.randint(3, 5), len(all_songs) - num_trending)
    rising_songs = random.sample([s for s in all_songs if s not in trending_songs], num_rising)
    
    # Chuẩn bị khoảng thời gian
    now = timezone.now()
    
    # 1. Tạo dữ liệu cho bài hát trending - nhiều lượt nghe trong 7 ngày qua
    for song in trending_songs:
        # Tạo khoảng 100-200 lượt nghe trong 7 ngày qua
        num_plays = random.randint(100, 200)
        
        for _ in range(num_plays):
            # Ngẫu nhiên thời gian trong 7 ngày qua
            random_days = random.uniform(0, 7)
            played_at = now - timedelta(days=random_days)
            
            # Ngẫu nhiên người dùng
            user = random.choice(users)
            
            # Tạo bản ghi lịch sử play
            SongPlayHistory.objects.create(
                user=user,
                song=song,
                played_at=played_at
            )
        
        # Cập nhật tổng số lượt play của bài hát
        song.play_count += num_plays
        song.save()
        
        print(f"Đã tạo {num_plays} lượt nghe trong 7 ngày qua cho bài hát trending: {song.title}")
    
    # 2. Tạo dữ liệu cho bài hát "rising" - nhiều lượt nghe trong 2 ngày gần đây
    for song in rising_songs:
        # Tạo khoảng 50-100 lượt nghe trong 2 ngày qua
        num_plays = random.randint(50, 100)
        
        for _ in range(num_plays):
            # Ngẫu nhiên thời gian trong 2 ngày qua (để tạo hiệu ứng mới nổi)
            random_days = random.uniform(0, 2)
            played_at = now - timedelta(days=random_days)
            
            # Ngẫu nhiên người dùng
            user = random.choice(users)
            
            # Tạo bản ghi lịch sử play
            SongPlayHistory.objects.create(
                user=user,
                song=song,
                played_at=played_at
            )
        
        # Cập nhật tổng số lượt play của bài hát
        song.play_count += num_plays
        song.save()
        
        print(f"Đã tạo {num_plays} lượt nghe trong 2 ngày qua cho bài hát đang nổi: {song.title}")
    
    # 3. Tạo thêm một số lượt nghe ngẫu nhiên cho các bài hát khác
    other_songs = [s for s in all_songs if s not in trending_songs and s not in rising_songs]
    for song in other_songs[:20]:  # Chỉ tạo cho 20 bài ngẫu nhiên
        # Tạo khoảng 5-20 lượt nghe
        num_plays = random.randint(5, 20)
        
        for _ in range(num_plays):
            # Ngẫu nhiên thời gian trong 7 ngày qua
            random_days = random.uniform(0, 7)
            played_at = now - timedelta(days=random_days)
            
            # Ngẫu nhiên người dùng
            user = random.choice(users)
            
            # Tạo bản ghi lịch sử play
            SongPlayHistory.objects.create(
                user=user,
                song=song,
                played_at=played_at
            )
        
        # Cập nhật tổng số lượt play của bài hát
        song.play_count += num_plays
        song.save()
    
    # Tạo thêm lượt thích cho bài hát trending
    for song in trending_songs:
        # Tăng lượt thích cho trending (thêm 10-20 lượt thích)
        like_increase = random.randint(10, 20)
        song.likes_count += like_increase
        song.save()
        
        # Liên kết users với bài hát ưa thích
        like_users = random.sample(users, min(like_increase, len(users)))
        for user in like_users:
            # Sử dụng hàm helper để tránh cảnh báo linter
            favorite_songs = safe_get_related_field(user, 'favorite_songs')
            if favorite_songs:
                try:
                    favorite_songs.add(song)
                except Exception as e:
                    print(f"Lỗi khi thêm bài hát vào danh sách yêu thích: {e}")
        
        print(f"Đã thêm {like_increase} lượt thích cho bài hát trending: {song.title}")
    
    print(f"""
    Hoàn thành tạo dữ liệu trending giả lập!
    - {len(trending_songs)} bài hát trending với nhiều lượt nghe trong 7 ngày
    - {len(rising_songs)} bài hát đang nổi với nhiều lượt nghe trong 2 ngày
    """)

if __name__ == "__main__":
    generate_trending_data()