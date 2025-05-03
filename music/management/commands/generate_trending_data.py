# Lưu file này với tên generate_trending_data.py
import os
import django
import random
from datetime import datetime, timedelta

# Thiết lập Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_chat.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.utils import timezone
from music.models import Song, SongPlayHistory, SearchHistory, Rating
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
    
    # Tăng số lượng bài hát trending (20-30 bài)
    num_trending = min(random.randint(20, 30), len(all_songs))
    trending_songs = random.sample(all_songs, num_trending)
    
    # Tăng số lượng bài hát "rising" (10-15 bài)
    num_rising = min(random.randint(10, 15), len(all_songs) - num_trending)
    rising_songs = random.sample([s for s in all_songs if s not in trending_songs], num_rising)
    
    # Chọn một số bài hát "genre-specific" cho mỗi người dùng
    # Giúp tạo ra nhiều đề xuất đa dạng theo thể loại
    user_genre_prefs = {}
    all_genres = set(song.genre for song in all_songs if song.genre)
    
    for user in users:
        # Mỗi người dùng thích 2-4 thể loại ngẫu nhiên
        num_genres = random.randint(2, 4)
        if all_genres:
            user_genre_prefs[user.id] = random.sample(list(all_genres), min(num_genres, len(all_genres)))
    
    # Chuẩn bị khoảng thời gian
    now = timezone.now()
    
    # 1. Tạo dữ liệu cho bài hát trending - nhiều lượt nghe trong 14 ngày qua (tăng từ 7 lên 14)
    for song in trending_songs:
        # Tăng số lượt nghe (150-300)
        num_plays = random.randint(150, 300)
        
        for _ in range(num_plays):
            # Ngẫu nhiên thời gian trong 14 ngày qua
            random_days = random.uniform(0, 14)
            played_at = now - timedelta(days=random_days)
            
            # Ngẫu nhiên người dùng - Nhưng có xu hướng ưu tiên những người thích thể loại của bài hát
            matching_users = [u for u in users if song.genre in user_genre_prefs.get(u.id, [])]
            if matching_users and random.random() > 0.3:  # 70% cơ hội chọn người dùng phù hợp
                user = random.choice(matching_users)
            else:
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
        
        print(f"Đã tạo {num_plays} lượt nghe trong 14 ngày qua cho bài hát trending: {song.title}")
    
    # 2. Tạo dữ liệu cho bài hát "rising" - nhiều lượt nghe trong 3 ngày gần đây (tăng từ 2 lên 3)
    for song in rising_songs:
        # Tăng số lượt nghe (70-150)
        num_plays = random.randint(70, 150)
        
        for _ in range(num_plays):
            # Ngẫu nhiên thời gian trong 3 ngày qua (để tạo hiệu ứng mới nổi)
            random_days = random.uniform(0, 3)
            played_at = now - timedelta(days=random_days)
            
            # Ngẫu nhiên người dùng - Tương tự như trên
            matching_users = [u for u in users if song.genre in user_genre_prefs.get(u.id, [])]
            if matching_users and random.random() > 0.3:
                user = random.choice(matching_users)
            else:
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
        
        print(f"Đã tạo {num_plays} lượt nghe trong 3 ngày qua cho bài hát đang nổi: {song.title}")
    
    # 3. Tạo thêm một số lượt nghe ngẫu nhiên cho các bài hát khác
    other_songs = [s for s in all_songs if s not in trending_songs and s not in rising_songs]
    for song in other_songs[:40]:  # Tăng số lượng từ 20 lên 40
        # Tạo khoảng 10-30 lượt nghe (tăng từ 5-20)
        num_plays = random.randint(10, 30)
        
        for _ in range(num_plays):
            # Ngẫu nhiên thời gian trong 14 ngày qua
            random_days = random.uniform(0, 14)
            played_at = now - timedelta(days=random_days)
            
            # Ngẫu nhiên người dùng với xu hướng thể loại
            matching_users = [u for u in users if song.genre in user_genre_prefs.get(u.id, [])]
            if matching_users and random.random() > 0.3:
                user = random.choice(matching_users)
            else:
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
        # Tăng lượt thích cho trending (thêm 15-30 lượt thích)
        like_increase = random.randint(15, 30)
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
            
            # Thêm đánh giá cao (4-5 sao) cho bài hát yêu thích
            if random.random() > 0.3:  # 70% cơ hội đánh giá cao
                try:
                    Rating.objects.create(
                        user=user,
                        song=song,
                        rating=random.randint(4, 5)
                    )
                except Exception as e:
                    print(f"Lỗi khi tạo đánh giá: {e}")
        
        print(f"Đã thêm {like_increase} lượt thích cho bài hát trending: {song.title}")
    
    # Thêm lịch sử tìm kiếm để cải thiện đề xuất dựa trên từ khóa
    search_terms = []
    for song in trending_songs[:10]:  # Chỉ lấy 10 bài hát trending đầu tiên
        # Tạo từ khóa tìm kiếm từ tiêu đề
        terms = song.title.split()
        if terms:
            search_terms.append(random.choice(terms))
        # Thêm từ khóa từ tên nghệ sĩ
        if song.artist:
            search_terms.append(song.artist)
    
    # Nếu có từ khóa tìm kiếm, tạo lịch sử tìm kiếm cho người dùng
    if search_terms:
        for user in users:
            # Mỗi người dùng tìm kiếm 3-7 từ khóa
            num_searches = random.randint(3, 7)
            user_search_terms = random.sample(search_terms, min(num_searches, len(search_terms)))
            
            for term in user_search_terms:
                # Tạo lịch sử tìm kiếm trong 14 ngày qua
                random_days = random.uniform(0, 14)
                search_time = now - timedelta(days=random_days)
                
                try:
                    SearchHistory.objects.create(
                        user=user,
                        query=term,
                        timestamp=search_time
                    )
                except Exception as e:
                    print(f"Lỗi khi tạo lịch sử tìm kiếm: {e}")
    
    print(f"""
    Hoàn thành tạo dữ liệu trending giả lập!
    - {len(trending_songs)} bài hát trending với nhiều lượt nghe trong 14 ngày
    - {len(rising_songs)} bài hát đang nổi với nhiều lượt nghe trong 3 ngày
    - Đã tạo dữ liệu nghe nhạc theo xu hướng thể loại cho {len(users)} người dùng
    - Đã tạo lịch sử tìm kiếm để cải thiện đề xuất dựa trên từ khóa
    """)

class Command(BaseCommand):
    help = 'Tạo dữ liệu trending giả lập cho bài hát'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Bắt đầu tạo dữ liệu trending...'))
        generate_trending_data()
        self.stdout.write(self.style.SUCCESS('Hoàn thành tạo dữ liệu trending!'))

if __name__ == "__main__":
    generate_trending_data()