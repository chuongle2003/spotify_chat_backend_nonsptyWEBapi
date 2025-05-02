import os
import django
import random
from datetime import datetime, timedelta

# Thiết lập Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_chat.settings')
django.setup()

from django.utils import timezone
from django.db.models import Count, F, Q
from music.models import (
    Song, Album, Artist, Genre, Playlist, 
    SongPlayHistory, Rating, Comment, SearchHistory
)
from django.contrib.auth import get_user_model
from utils.pylance_helpers import safe_get_related_field

User = get_user_model()

class RealisticActivityGenerator:
    """
    Tạo dữ liệu hoạt động người dùng thực tế dựa trên dữ liệu hiện có.
    Khác với trending data, lớp này tạo ra hoạt động dựa trên thói quen thực tế:
    - Người dùng thường nghe lại bài hát họ yêu thích
    - Người dùng thường nghe nhiều bài hát trong cùng một thể loại
    - Có những người dùng rất tích cực và những người ít hoạt động
    """
    def __init__(self):
        self.users = list(User.objects.all())
        self.songs = list(Song.objects.all())
        self.all_genres = list(set(song.genre for song in self.songs if song.genre))
        self.now = timezone.now()
        
        # Chia người dùng thành nhóm theo mức độ hoạt động
        random.shuffle(self.users)
        user_count = len(self.users)
        self.active_users = self.users[:int(user_count * 0.2)]  # 20% người dùng rất tích cực
        self.moderate_users = self.users[int(user_count * 0.2):int(user_count * 0.6)]  # 40% người dùng bình thường
        self.casual_users = self.users[int(user_count * 0.6):]  # 40% người dùng thỉnh thoảng
        
        # Báo cáo trước khi bắt đầu
        print(f"Đã tìm thấy {len(self.users)} người dùng")
        print(f"Đã tìm thấy {len(self.songs)} bài hát")
        print(f"Đã tìm thấy {len(self.all_genres)} thể loại")
        
    def run(self):
        """Chạy toàn bộ quá trình tạo dữ liệu"""
        print("Bắt đầu tạo dữ liệu hoạt động thực tế...")
        self.generate_user_preferences()
        self.generate_play_history(days=90)  # 3 tháng dữ liệu nghe
        self.generate_comments_and_ratings()
        self.generate_search_history()
        self.update_song_statistics()
        print("Hoàn thành tạo dữ liệu hoạt động thực tế!")
        
    def generate_user_preferences(self):
        """Tạo sở thích cho mỗi người dùng"""
        print("Tạo sở thích người dùng...")
        
        for user in self.users:
            # Mỗi người dùng thích 1-3 thể loại chính
            num_fav_genres = random.randint(1, min(3, len(self.all_genres)))
            user_genres = random.sample(self.all_genres, num_fav_genres)
            
            # Lấy bài hát từ các thể loại yêu thích
            genre_songs = [song for song in self.songs if song.genre in user_genres]
            
            # Mỗi người dùng thích một số bài hát từ thể loại yêu thích
            if genre_songs:
                num_fav_songs = 0
                if user in self.active_users:
                    num_fav_songs = random.randint(10, 30)
                elif user in self.moderate_users:
                    num_fav_songs = random.randint(5, 15)
                else:  # casual users
                    num_fav_songs = random.randint(1, 8)
                
                num_fav_songs = min(num_fav_songs, len(genre_songs))
                favorite_songs = random.sample(genre_songs, num_fav_songs)
                
                # Thêm vào favorite - kiểm tra an toàn
                for song in favorite_songs:
                    try:
                        # Sử dụng helper để tránh cảnh báo linter
                        user_favorites = safe_get_related_field(user, 'favorite_songs')
                        if user_favorites:
                            user_favorites.add(song)
                        # Tăng lượt thích cho bài hát
                        song.likes_count += 1
                        song.save()
                    except Exception as e:
                        print(f"Lỗi khi thêm bài hát yêu thích: {e}")
        
        print("Đã tạo xong sở thích người dùng")
    
    def generate_play_history(self, days=90):
        """Tạo lịch sử nghe nhạc trong khoảng thời gian"""
        print(f"Tạo lịch sử nghe nhạc trong {days} ngày...")
        
        # Tổng số lượt play dự kiến
        total_plays = 0
        
        # Sử dụng random thay cho numpy để tạo trọng số ngày (0.7-1.3)
        day_weights = [0.7 + random.random() * 0.6 for _ in range(days)]
        
        # Tạo dữ liệu nghe cho từng nhóm người dùng
        for user in self.users:
            # Xác định số bài hát user đã nghe dựa vào nhóm
            daily_plays = 0
            if user in self.active_users:
                daily_plays = random.randint(15, 30)  # Nghe nhiều nhạc mỗi ngày
            elif user in self.moderate_users:
                daily_plays = random.randint(5, 15)  # Nghe vừa phải
            else:  # casual users
                daily_plays = random.randint(0, 5)  # Nghe ít hoặc không nghe hàng ngày
            
            # Có một số ngày không nghe nhạc
            active_days = random.sample(range(days), int(days * (0.8 if user in self.active_users else 0.5 if user in self.moderate_users else 0.3)))
            
            # Lấy bài hát yêu thích của user
            fav_songs = []
            # Sử dụng helper thay vì truy cập trực tiếp
            user_favorites = safe_get_related_field(user, 'favorite_songs')
            if user_favorites:
                try:
                    fav_songs = list(user_favorites.all())
                except:
                    fav_songs = []
            
            for day_offset in active_days:
                # Áp dụng trọng số ngày cho số lượt nghe
                day_factor = day_weights[day_offset]
                daily_play_count = max(1, int(daily_plays * day_factor))
                
                # Tạo ngày cụ thể
                current_day = self.now - timedelta(days=day_offset)
                
                # 60-80% lượt nghe là từ bài hát yêu thích
                fav_plays = min(len(fav_songs), int(daily_play_count * random.uniform(0.6, 0.8))) if fav_songs else 0
                other_plays = daily_play_count - fav_plays
                
                # Tạo lịch sử nghe cho bài hát yêu thích
                if fav_plays > 0:
                    for _ in range(fav_plays):
                        song = random.choice(fav_songs)
                        
                        # Tạo thời gian nghe ngẫu nhiên trong ngày
                        hour = random.randint(7, 23)  # 7 sáng - 11 tối
                        minute = random.randint(0, 59)
                        second = random.randint(0, 59)
                        
                        played_at = current_day.replace(hour=hour, minute=minute, second=second)
                        
                        # Tạo lịch sử nghe
                        SongPlayHistory.objects.create(
                            user=user,
                            song=song,
                            played_at=played_at
                        )
                        total_plays += 1
                
                # Tạo lịch sử nghe cho các bài hát khác
                if other_plays > 0:
                    # Ưu tiên bài hát cùng thể loại yêu thích
                    fav_genres = set()
                    for song in fav_songs:
                        if song.genre:
                            fav_genres.add(song.genre)
                    
                    similar_songs = [song for song in self.songs if song.genre in fav_genres and song not in fav_songs]
                    
                    for _ in range(other_plays):
                        # 70% khả năng chọn bài hát cùng thể loại yêu thích, 30% hoàn toàn ngẫu nhiên
                        if similar_songs and random.random() < 0.7:
                            song = random.choice(similar_songs)
                        else:
                            song = random.choice(self.songs)
                        
                        # Tạo thời gian nghe ngẫu nhiên trong ngày
                        hour = random.randint(7, 23)
                        minute = random.randint(0, 59)
                        second = random.randint(0, 59)
                        
                        played_at = current_day.replace(hour=hour, minute=minute, second=second)
                        
                        # Tạo lịch sử nghe
                        SongPlayHistory.objects.create(
                            user=user,
                            song=song,
                            played_at=played_at
                        )
                        total_plays += 1
        
        print(f"Đã tạo {total_plays} lượt nghe nhạc trong {days} ngày")
    
    def generate_comments_and_ratings(self):
        """Tạo bình luận và đánh giá"""
        print("Tạo bình luận và đánh giá...")
        
        # Danh sách bình luận mẫu
        positive_comments = [
            "Bài hát tuyệt vời! Rất thích giai điệu",
            "Ca sĩ hát quá hay, tôi đã nghe đi nghe lại nhiều lần",
            "Bài hát này làm tôi nhớ về kỷ niệm đẹp",
            "Beat cực chất, nghe mãi không chán",
            "Cao trào của bài hát thật sự rất hay",
            "Ca từ hay, ý nghĩa và sâu lắng",
            "Nhạc dễ nghe, dễ thuộc và rất cuốn",
            "Đây là một trong những bài hát tôi thích nhất",
            "Bài này đúng gu của tôi",
            "Quá đỉnh, đúng là nghệ sĩ tài năng"
        ]
        
        neutral_comments = [
            "Bài hát khá ổn",
            "Nghe được, không quá nổi bật",
            "Ca từ bình thường nhưng beat hay",
            "Giọng ca được nhưng sản xuất chưa tốt lắm",
            "Bài này nghe cũng được",
            "Không quá xuất sắc nhưng cũng không tệ",
            "Chắc phải nghe thêm vài lần nữa mới quen",
            "Khá là basic nhưng vẫn ok",
            "Tôi thấy bài này bình thường",
            "Không phải gu của tôi nhưng vẫn nghe được"
        ]
        
        negative_comments = [
            "Bài hát không hay lắm",
            "Tôi không thích giai điệu này",
            "Ca từ khá nhạt và thiếu chiều sâu",
            "Beat không nổi bật, hơi đơn điệu",
            "Không phù hợp với phong cách âm nhạc tôi thích",
            "Hơi thất vọng với sản phẩm này",
            "Không đúng kỳ vọng của tôi",
            "Tôi mong đợi nhiều hơn từ nghệ sĩ này",
            "Bài này không bằng các bài trước đây",
            "Hơi chán, không có điểm nhấn"
        ]
        
        # Số lượng bình luận dự kiến
        comment_count = 0
        rating_count = 0
        
        # Tạo bình luận và đánh giá cho từng nhóm người dùng
        for user in self.users:
            # Xác định số bài hát user sẽ bình luận/đánh giá
            if user in self.active_users:
                num_comments = random.randint(5, 15)
                num_ratings = random.randint(10, 30)
            elif user in self.moderate_users:
                num_comments = random.randint(1, 7)
                num_ratings = random.randint(5, 15)
            else:  # casual users
                num_comments = random.randint(0, 3)
                num_ratings = random.randint(0, 8)
            
            # Chọn bài hát để bình luận/đánh giá, ưu tiên bài hát yêu thích
            fav_songs = []
            # Sử dụng helper thay vì truy cập trực tiếp
            user_favorites = safe_get_related_field(user, 'favorite_songs')
            if user_favorites:
                try:
                    fav_songs = list(user_favorites.all())
                except:
                    fav_songs = []
            
            # Tạo bình luận
            comment_songs = []
            if fav_songs and num_comments > 0:
                # Ưu tiên bình luận bài hát yêu thích
                comment_songs = random.sample(fav_songs, min(len(fav_songs), num_comments))
                
                # Bổ sung thêm nếu không đủ
                if len(comment_songs) < num_comments:
                    remaining = num_comments - len(comment_songs)
                    other_songs = [s for s in self.songs if s not in comment_songs]
                    comment_songs.extend(random.sample(other_songs, min(remaining, len(other_songs))))
            elif num_comments > 0:
                # Chọn ngẫu nhiên nếu không có bài yêu thích
                comment_songs = random.sample(self.songs, min(num_comments, len(self.songs)))
            
            for song in comment_songs:
                # Chọn loại bình luận dựa trên xác suất
                # Người dùng có xu hướng bình luận tích cực cho bài hát họ yêu thích
                if song in fav_songs:
                    comment_type = random.choices(["positive", "neutral", "negative"], weights=[0.8, 0.15, 0.05])[0]
                else:
                    comment_type = random.choices(["positive", "neutral", "negative"], weights=[0.4, 0.4, 0.2])[0]
                
                # Chọn ngẫu nhiên bình luận từ danh sách
                if comment_type == "positive":
                    comment_text = random.choice(positive_comments)
                elif comment_type == "neutral":
                    comment_text = random.choice(neutral_comments)
                else:
                    comment_text = random.choice(negative_comments)
                
                # Tạo thời gian bình luận ngẫu nhiên trong 60 ngày qua
                days_ago = random.randint(0, 60)
                commented_at = self.now - timedelta(days=days_ago)
                
                # Tạo bình luận
                Comment.objects.create(
                    user=user,
                    song=song,
                    content=comment_text,
                    created_at=commented_at
                )
                comment_count += 1
            
            # Tạo đánh giá
            rating_songs = []
            if fav_songs and num_ratings > 0:
                # Ưu tiên đánh giá bài hát yêu thích
                rating_songs = random.sample(fav_songs, min(len(fav_songs), num_ratings))
                
                # Bổ sung thêm nếu không đủ
                if len(rating_songs) < num_ratings:
                    remaining = num_ratings - len(rating_songs)
                    other_songs = [s for s in self.songs if s not in rating_songs]
                    rating_songs.extend(random.sample(other_songs, min(remaining, len(other_songs))))
            elif num_ratings > 0:
                # Chọn ngẫu nhiên nếu không có bài yêu thích
                rating_songs = random.sample(self.songs, min(num_ratings, len(self.songs)))
            
            # Lấy tất cả các bài hát đã được đánh giá của user
            rated_songs = set(Rating.objects.filter(user=user).values_list('song_id', flat=True))
            
            for song in rating_songs:
                # Kiểm tra xem đã đánh giá chưa (tránh unique constraint)
                if song.id in rated_songs:
                    continue
                    
                # Người dùng có xu hướng đánh giá cao bài hát họ yêu thích
                if song in fav_songs:
                    score = random.randint(4, 5)
                else:
                    score = random.randint(1, 5)
                
                # Tạo thời gian đánh giá ngẫu nhiên trong 60 ngày qua
                days_ago = random.randint(0, 60)
                rated_at = self.now - timedelta(days=days_ago)
                
                try:
                    # Tạo đánh giá
                    Rating.objects.create(
                        user=user,
                        song=song,
                        rating=score,
                        created_at=rated_at
                    )
                    rating_count += 1
                    rated_songs.add(song.id)  # Thêm vào danh sách đã đánh giá
                except Exception as e:
                    print(f"Lỗi khi đánh giá bài hát {song.title}: {e}")
        
        print(f"Đã tạo {comment_count} bình luận và {rating_count} đánh giá")
    
    def generate_search_history(self):
        """Tạo lịch sử tìm kiếm"""
        print("Tạo lịch sử tìm kiếm...")
        
        # Danh sách từ khóa tìm kiếm mẫu
        search_keywords = [
            "nhạc trẻ", "nhạc pop", "nhạc rock", "bài hát hay nhất", "ca khúc mới",
            "bài hát buồn", "nhạc acoustic", "nhạc EDM", "nhạc chill", "nhạc remix",
            "top hits", "bài hát tâm trạng", "nhạc tiếng anh", "ballad", "nhạc rap"
        ]
        
        # Thêm tên nghệ sĩ và tên bài hát vào từ khóa
        artist_names = set(song.artist for song in self.songs if song.artist)
        search_keywords.extend(list(artist_names)[:15])  # Thêm tối đa 15 nghệ sĩ
        
        song_titles = [song.title for song in self.songs]
        search_keywords.extend(random.sample(song_titles, min(15, len(song_titles))))  # Thêm tối đa 15 bài hát
        
        # Tạo lịch sử tìm kiếm cho từng người dùng
        search_count = 0
        
        for user in self.users:
            # Xác định số lần tìm kiếm dựa vào mức độ hoạt động
            if user in self.active_users:
                num_searches = random.randint(20, 50)
            elif user in self.moderate_users:
                num_searches = random.randint(5, 20)
            else:  # casual users
                num_searches = random.randint(0, 10)
            
            for _ in range(num_searches):
                # Chọn từ khóa tìm kiếm
                keyword = random.choice(search_keywords)
                
                # Tạo thời gian tìm kiếm trong 30 ngày qua
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                
                searched_at = self.now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
                
                # Tạo lịch sử tìm kiếm
                SearchHistory.objects.create(
                    user=user,
                    query=keyword,
                    timestamp=searched_at
                )
                search_count += 1
        
        print(f"Đã tạo {search_count} lịch sử tìm kiếm")
    
    def update_song_statistics(self):
        """Cập nhật thống kê bài hát dựa trên lịch sử nghe"""
        print("Cập nhật thống kê bài hát...")
        
        # Cập nhật số lượt nghe cho mỗi bài hát
        for song in self.songs:
            play_count = SongPlayHistory.objects.filter(song=song).count()
            song.play_count = play_count
            song.save()
        
        print("Đã cập nhật thống kê bài hát")

# Chạy script nếu thực thi trực tiếp
if __name__ == "__main__":
    generator = RealisticActivityGenerator()
    generator.run() 