import os
import django
import random
from datetime import datetime, timedelta
import argparse

# Thiết lập Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_chat.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, F, Q, Sum
from music.models import (
    Song, Playlist, SongPlayHistory, Genre, 
    Rating, UserActivity, Album, Artist, UserRecommendation
)
from django.contrib.auth import get_user_model
from music.utils import generate_song_recommendations
from tqdm import tqdm

User = get_user_model()

class RecommendationDataGenerator:
    """
    Tạo dữ liệu gợi ý âm nhạc cho người dùng dựa trên:
    1. Lịch sử nghe nhạc
    2. Thể loại yêu thích
    3. Bài hát đã thích
    4. Đánh giá cao
    Từ đó tạo ra các bộ dữ liệu để hệ thống gợi ý có thể hoạt động tốt.
    """
    
    def __init__(self, clear_existing=False, target_users=None):
        """
        Khởi tạo generator
        
        Args:
            clear_existing: Xóa dữ liệu lịch sử nghe cũ
            target_users: Danh sách user_id cụ thể để tạo dữ liệu, nếu None thì tạo cho tất cả
        """
        self.users = User.objects.all()
        if target_users:
            self.users = self.users.filter(id__in=target_users)
        
        self.songs = list(Song.objects.all())
        self.all_genres = list(set(song.genre for song in self.songs if song.genre))
        self.now = timezone.now()
        
        if clear_existing and self.users:
            # Xóa lịch sử nghe cũ của các user được chọn
            SongPlayHistory.objects.filter(user__in=self.users).delete()
            print(f"Đã xóa lịch sử nghe cũ của {self.users.count()} người dùng")
        
        # Chia người dùng thành nhóm theo mức độ hoạt động
        self.users = list(self.users)
        random.shuffle(self.users)
        user_count = len(self.users)
        
        if user_count > 0:
            self.active_users = self.users[:max(1, int(user_count * 0.2))]  # 20% người dùng rất tích cực
            self.moderate_users = self.users[int(user_count * 0.2):int(user_count * 0.6)]  # 40% người dùng bình thường
            self.casual_users = self.users[int(user_count * 0.6):]  # 40% người dùng thỉnh thoảng
        else:
            self.active_users = []
            self.moderate_users = []
            self.casual_users = []
        
        # Báo cáo trước khi bắt đầu
        print(f"Đã tìm thấy {len(self.users)} người dùng")
        print(f"Đã tìm thấy {len(self.songs)} bài hát")
        print(f"Đã tìm thấy {len(self.all_genres)} thể loại")
    
    def run(self, days=30):
        """
        Chạy toàn bộ quá trình tạo dữ liệu
        
        Args:
            days: Số ngày dữ liệu lịch sử cần tạo
        """
        print(f"Bắt đầu tạo dữ liệu gợi ý âm nhạc trong {days} ngày...")
        
        if not self.users:
            print("Không có người dùng nào để tạo dữ liệu!")
            return
            
        if not self.songs:
            print("Không có bài hát nào để tạo dữ liệu!")
            return
        
        # 1. Tạo sở thích thể loại cho người dùng
        self._generate_genre_preferences()
        
        # 2. Tạo lịch sử nghe nhạc dựa trên sở thích thể loại
        self._generate_play_history(days)
        
        # 3. Tạo dữ liệu bài hát yêu thích dựa trên lịch sử nghe và sở thích
        self._generate_favorite_songs()
        
        # 4. Tạo đánh giá bài hát
        self._generate_ratings()
        
        # 5. Phân tích và báo cáo sự phù hợp của dữ liệu gợi ý đã tạo
        self._analyze_recommendation_data()
        
        print("Hoàn thành tạo dữ liệu gợi ý âm nhạc!")
    
    def _generate_genre_preferences(self):
        """Tạo sở thích thể loại cho người dùng"""
        print("Tạo sở thích thể loại cho người dùng...")
        
        # Lưu sở thích thể loại vào biến để sử dụng sau
        self.user_genre_preferences = {}
        
        for user in self.users:
            # Chọn số lượng thể loại yêu thích dựa vào nhóm người dùng
            if user in self.active_users:
                num_preferred_genres = random.randint(3, 6)  # Người tích cực có nhiều thể loại yêu thích
            elif user in self.moderate_users:
                num_preferred_genres = random.randint(2, 4)  # Người dùng bình thường
            else:
                num_preferred_genres = random.randint(1, 3)  # Người dùng thỉnh thoảng
            
            # Chọn ngẫu nhiên các thể loại yêu thích
            if self.all_genres:
                preferred_genres = random.sample(self.all_genres, min(num_preferred_genres, len(self.all_genres)))
                
                # Gán mức độ yêu thích (0.5-1.0) cho từng thể loại
                self.user_genre_preferences[user.id] = {
                    genre: 0.5 + random.random() * 0.5 
                    for genre in preferred_genres
                }
                
        print(f"Đã tạo sở thích thể loại cho {len(self.user_genre_preferences)} người dùng")
    
    def _generate_play_history(self, days=30):
        """
        Tạo lịch sử nghe nhạc dựa trên sở thích thể loại
        
        Args:
            days: Số ngày lịch sử cần tạo
        """
        print(f"Tạo lịch sử nghe nhạc trong {days} ngày...")
        
        # Tổng số lượt play được tạo
        total_plays = 0
        
        # Tạo trọng số cho các ngày (ngày gần đây có xu hướng nhiều lượt nghe hơn)
        day_weights = [(0.7 + i * 0.3/days) for i in range(days)]
        
        # Tạo lịch sử nghe cho từng người dùng
        for user in self.users:
            # Xác định số bài hát nghe mỗi ngày dựa vào nhóm người dùng
            if user in self.active_users:
                base_daily_plays = random.randint(10, 25)
            elif user in self.moderate_users:
                base_daily_plays = random.randint(5, 15)
            else:  # casual users
                base_daily_plays = random.randint(0, 5)
            
            # Chọn những ngày người dùng nghe nhạc
            if user in self.active_users:
                active_ratio = 0.8  # Nghe nhạc 80% số ngày
            elif user in self.moderate_users:
                active_ratio = 0.6  # Nghe nhạc 60% số ngày
            else:
                active_ratio = 0.3  # Nghe nhạc 30% số ngày
            
            active_days = random.sample(range(days), int(days * active_ratio))
            
            # Lấy thể loại yêu thích của người dùng
            preferred_genres = self.user_genre_preferences.get(user.id, {})
            
            # Tìm bài hát trong các thể loại yêu thích
            genre_songs = {}
            for genre, weight in preferred_genres.items():
                genre_songs[genre] = [song for song in self.songs if song.genre == genre]
            
            # Chọn một số bài hát yêu thích để nghe nhiều lần
            favorite_pool = []
            for genre, songs in genre_songs.items():
                if songs:
                    weight = preferred_genres[genre]
                    num_favorites = max(1, int(len(songs) * 0.2))  # Lấy tối đa 20% bài hát làm yêu thích
                    favorites = random.sample(songs, min(num_favorites, len(songs)))
                    for song in favorites:
                        favorite_pool.append((song, weight))
            
            # Nếu không có bài hát yêu thích nào, lấy một số bài ngẫu nhiên
            if not favorite_pool:
                favorite_pool = [(random.choice(self.songs), 0.5) for _ in range(3)]
            
            # Duyệt qua từng ngày và tạo lịch sử nghe
            for day_index in range(days):
                if day_index not in active_days:
                    continue
                
                current_day = self.now - timedelta(days=days-day_index-1)
                daily_plays = int(base_daily_plays * day_weights[day_index])
                
                # Phân bổ số lượt nghe giữa bài yêu thích và bài khác
                fav_ratio = 0.6  # 60% nghe bài yêu thích, 40% khám phá bài mới
                fav_plays = int(daily_plays * fav_ratio)
                other_plays = daily_plays - fav_plays
                
                # Nghe bài yêu thích
                for _ in range(fav_plays):
                    song, weight = random.choice(favorite_pool)
                    
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
                
                # Nghe các bài khác (khám phá)
                for _ in range(other_plays):
                    # 70% khả năng nghe bài cùng thể loại yêu thích, 30% hoàn toàn ngẫu nhiên
                    if preferred_genres and random.random() < 0.7:
                        # Chọn một thể loại yêu thích
                        genre = random.choices(
                            list(preferred_genres.keys()),
                            weights=list(preferred_genres.values()),
                            k=1
                        )[0]
                        
                        # Tìm bài hát trong thể loại đó
                        genre_songs_list = [song for song in self.songs if song.genre == genre]
                        if genre_songs_list:
                            song = random.choice(genre_songs_list)
                        else:
                            song = random.choice(self.songs)
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
    
    def _generate_favorite_songs(self):
        """Tạo dữ liệu bài hát yêu thích dựa trên lịch sử nghe và sở thích"""
        print("Tạo dữ liệu bài hát yêu thích...")
        
        for user in self.users:
            # Xóa danh sách yêu thích hiện tại
            user.favorite_songs.clear()
            
            # Lấy bài hát đã nghe nhiều nhất
            top_played_songs = SongPlayHistory.objects.filter(user=user) \
                .values('song') \
                .annotate(play_count=Count('song')) \
                .order_by('-play_count')
            
            # Xác định số lượng bài hát yêu thích tùy theo nhóm người dùng
            if user in self.active_users:
                fav_count = random.randint(10, 20)
            elif user in self.moderate_users:
                fav_count = random.randint(5, 15)
            else:  # casual users
                fav_count = random.randint(1, 8)
            
            # Lấy ID của bài hát được nghe nhiều nhất
            top_song_ids = [item['song'] for item in top_played_songs[:fav_count * 2]]
            
            # Chọn ngẫu nhiên từ top bài hát nghe nhiều
            if top_song_ids:
                # Lấy ít hơn số lượng bài hát nghe nhiều nếu không đủ
                num_to_select = min(fav_count, len(top_song_ids))
                selected_ids = random.sample(top_song_ids, num_to_select)
                
                # Thêm vào danh sách yêu thích
                favorite_songs = Song.objects.filter(id__in=selected_ids)
                for song in favorite_songs:
                    user.favorite_songs.add(song)
                    
                    # Tăng likes_count cho bài hát
                    song.likes_count += 1
                    song.save()
                    
                    # Lưu hoạt động yêu thích
                    UserActivity.objects.create(
                        user=user,
                        activity_type='LIKE',
                        song=song,
                        timestamp=self.now - timedelta(days=random.randint(0, 30))
                    )
            
            print(f"Đã tạo {user.favorite_songs.count()} bài hát yêu thích cho {user.username}")
    
    def _generate_ratings(self):
        """Tạo đánh giá bài hát"""
        print("Tạo đánh giá bài hát...")
        
        # Tổng số đánh giá được tạo
        rating_count = 0
        
        for user in self.users:
            # Xác định số lượng bài hát đánh giá
            if user in self.active_users:
                num_ratings = random.randint(15, 30)
            elif user in self.moderate_users:
                num_ratings = random.randint(5, 15)
            else:  # casual users
                num_ratings = random.randint(0, 5)
            
            # Lấy bài hát yêu thích của user
            fav_songs = list(user.favorite_songs.all())
            
            # Lấy bài hát đã nghe từ lịch sử
            played_songs = list(set(
                SongPlayHistory.objects.filter(user=user).values_list('song', flat=True)
            ))
            played_songs = Song.objects.filter(id__in=played_songs)
            
            # Ưu tiên đánh giá bài hát yêu thích
            rating_songs = []
            if fav_songs and num_ratings > 0:
                rating_songs = random.sample(fav_songs, min(len(fav_songs), num_ratings))
                
                # Bổ sung thêm nếu không đủ
                if len(rating_songs) < num_ratings:
                    remaining = num_ratings - len(rating_songs)
                    other_played = [s for s in played_songs if s not in rating_songs]
                    if other_played:
                        rating_songs.extend(random.sample(other_played, min(remaining, len(other_played))))
            
            elif played_songs and num_ratings > 0:
                rating_songs = random.sample(list(played_songs), min(num_ratings, played_songs.count()))
            
            # Lấy tất cả các bài hát đã được đánh giá của user
            rated_songs = set(Rating.objects.filter(user=user).values_list('song_id', flat=True))
            
            for song in rating_songs:
                # Kiểm tra xem đã đánh giá chưa (tránh unique constraint)
                if song.id in rated_songs:
                    continue
                    
                # Người dùng có xu hướng đánh giá cao bài hát họ yêu thích
                if song in fav_songs:
                    score = random.randint(4, 5)  # 4-5 sao
                else:
                    score = random.randint(2, 5)  # 2-5 sao
                
                # Tạo thời gian đánh giá ngẫu nhiên
                days_ago = random.randint(0, 30)
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
                    rated_songs.add(song.id)
                except Exception as e:
                    print(f"Lỗi khi tạo đánh giá: {e}")
        
        print(f"Đã tạo {rating_count} đánh giá bài hát")
    
    def _analyze_recommendation_data(self):
        """Phân tích và báo cáo sự phù hợp của dữ liệu gợi ý đã tạo"""
        print("\n=== Phân tích dữ liệu gợi ý ===")
        
        # Số lượng người dùng có dữ liệu gợi ý
        users_with_history = User.objects.annotate(
            history_count=Count('play_history')
        ).filter(history_count__gt=0).count()
        
        users_with_favorites = User.objects.annotate(
            fav_count=Count('favorite_songs')
        ).filter(fav_count__gt=0).count()
        
        users_with_ratings = User.objects.annotate(
            rating_count=Count('rating')
        ).filter(rating_count__gt=0).count()
        
        print(f"- Người dùng có lịch sử nghe: {users_with_history}/{len(self.users)}")
        print(f"- Người dùng có bài hát yêu thích: {users_with_favorites}/{len(self.users)}")
        print(f"- Người dùng có đánh giá bài hát: {users_with_ratings}/{len(self.users)}")
        
        # Phân tích sự phù hợp giữa lịch sử nghe và thể loại yêu thích
        genre_consistency = 0
        
        for user in self.users:
            # Lấy thể loại từ lịch sử nghe
            played_genres = {}
            for play in SongPlayHistory.objects.filter(user=user).select_related('song'):
                genre = play.song.genre
                if genre:
                    played_genres[genre] = played_genres.get(genre, 0) + 1
            
            # Lấy thể loại từ bài hát yêu thích
            fav_genres = {}
            for song in user.favorite_songs.all():
                genre = song.genre
                if genre:
                    fav_genres[genre] = fav_genres.get(genre, 0) + 1
            
            # Tính độ tương đồng giữa played_genres và fav_genres
            if played_genres and fav_genres:
                # Tìm các thể loại chung
                common_genres = set(played_genres.keys()) & set(fav_genres.keys())
                if common_genres:
                    genre_consistency += 1
        
        if users_with_history > 0 and users_with_favorites > 0:
            genre_consistency_pct = (genre_consistency / min(users_with_history, users_with_favorites)) * 100
            print(f"- Độ tương đồng giữa lịch sử nghe và bài hát yêu thích: {genre_consistency_pct:.2f}%")
        
        # Kiểm tra phân bố đánh giá
        ratings_dist = {}
        for i in range(1, 6):
            count = Rating.objects.filter(rating=i).count()
            ratings_dist[i] = count
        
        total_ratings = sum(ratings_dist.values())
        if total_ratings > 0:
            print("- Phân bố đánh giá:")
            for rating, count in ratings_dist.items():
                percentage = (count / total_ratings) * 100
                print(f"  {rating} sao: {count} ({percentage:.2f}%)")


class Command(BaseCommand):
    help = 'Tạo đề xuất âm nhạc cho tất cả người dùng'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Số lượng bài hát đề xuất cho mỗi người dùng'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=None,
            help='Chỉ tạo đề xuất cho người dùng cụ thể (tùy chọn)'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        user_id = options['user_id']
        
        self.stdout.write(self.style.SUCCESS(f'Bắt đầu tạo đề xuất âm nhạc...'))
        
        if user_id:
            # Nếu chỉ định một người dùng cụ thể
            try:
                user = User.objects.get(id=user_id)
                self._generate_user_recommendations(user, limit)
                self.stdout.write(self.style.SUCCESS(
                    f'Đã tạo {limit} đề xuất cho người dùng {user.username} (ID: {user.id})'
                ))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Không tìm thấy người dùng với ID {user_id}'))
                return
        else:
            # Tạo đề xuất cho tất cả người dùng
            users = User.objects.all()
            total_users = users.count()
            
            self.stdout.write(self.style.SUCCESS(f'Đang tạo đề xuất cho {total_users} người dùng...'))
            
            for user in tqdm(users, desc="Đang xử lý người dùng"):
                recommendations = self._generate_user_recommendations(user, limit)
                
            self.stdout.write(self.style.SUCCESS(
                f'Hoàn thành! Đã tạo đề xuất cho {total_users} người dùng.'
            ))
    
    def _generate_user_recommendations(self, user, limit):
        """Tạo đề xuất cho một người dùng"""
        try:
            # Xóa các đề xuất cũ
            UserRecommendation.objects.filter(user=user).delete()
            
            # Tạo đề xuất mới
            recommendations = generate_song_recommendations(user, limit=limit)
            
            # Lưu đề xuất vào database
            if recommendations:
                for i, song in enumerate(recommendations):
                    # Tính điểm đề xuất (cao nhất ở đầu danh sách)
                    score = 1.0 - (i / len(recommendations))
                    UserRecommendation.objects.create(
                        user=user,
                        song=song,
                        score=score
                    )
                    
                # In chi tiết đề xuất
                self.stdout.write(self.style.SUCCESS(f'Đề xuất cho {user.username}:'))
                for i, song in enumerate(recommendations, 1):
                    self.stdout.write(f'  {i}. {song.title} - {song.artist} (genre: {song.genre})')
            else:
                self.stdout.write(self.style.WARNING(f'Không có đề xuất nào cho {user.username}'))
            
            return recommendations
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Lỗi khi tạo đề xuất cho người dùng {user.username}: {str(e)}'
            ))
            return [] 