from django.core.management.base import BaseCommand
import random
from datetime import datetime, timedelta
from django.utils import timezone
from music.models import SongPlayHistory, Song
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Xóa lịch sử nghe nhạc cũ và tạo lịch sử mới phù hợp với API được sửa đổi'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Số ngày lịch sử phát sẽ được tạo'
        )
        parser.add_argument(
            '--keep-existing',
            action='store_true',
            help='Không xóa dữ liệu cũ trước khi tạo mới'
        )

    def handle(self, *args, **options):
        days = options['days']
        keep_existing = options['keep_existing']

        if not keep_existing:
            self.stdout.write(self.style.WARNING('Đang xóa tất cả lịch sử phát cũ...'))
            SongPlayHistory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Đã xóa tất cả lịch sử phát cũ!'))

        self.stdout.write(self.style.WARNING(f'Bắt đầu tạo lịch sử phát mới trong {days} ngày...'))
        
        # Đếm tổng số lượt tạo
        total_plays = 0
        
        # Lấy tất cả người dùng và bài hát
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR('Không tìm thấy người dùng nào. Vui lòng tạo dữ liệu người dùng trước.'))
            return
            
        songs = list(Song.objects.all())
        if not songs:
            self.stdout.write(self.style.ERROR('Không tìm thấy bài hát nào. Vui lòng tạo dữ liệu bài hát trước.'))
            return
            
        # Thời điểm hiện tại
        now = timezone.now()
        
        # Chia người dùng thành nhóm theo mức độ hoạt động
        random.shuffle(users)
        user_count = len(users)
        active_users = users[:int(user_count * 0.2)]  # 20% người dùng rất tích cực
        moderate_users = users[int(user_count * 0.2):int(user_count * 0.6)]  # 40% người dùng bình thường
        casual_users = users[int(user_count * 0.6):]  # 40% người dùng thỉnh thoảng
        
        # Báo cáo thông tin
        self.stdout.write(f"Đã tìm thấy {len(users)} người dùng")
        self.stdout.write(f"Đã tìm thấy {len(songs)} bài hát")
        
        # Tạo trọng số ngày (một số ngày sẽ có nhiều hoạt động hơn)
        day_weights = [0.7 + random.random() * 0.6 for _ in range(days)]
        
        # Tạo dữ liệu nghe cho từng người dùng
        for user in users:
            # Xác định số bài hát user đã nghe dựa vào nhóm
            base_daily_plays = 0
            if user in active_users:
                base_daily_plays = random.randint(15, 30)  # Nghe nhiều nhạc mỗi ngày
            elif user in moderate_users:
                base_daily_plays = random.randint(5, 15)  # Nghe vừa phải
            else:  # casual users
                base_daily_plays = random.randint(0, 5)  # Nghe ít
            
            # Có một số ngày không nghe nhạc
            active_ratio = 0.8 if user in active_users else 0.5 if user in moderate_users else 0.3
            active_days = random.sample(range(days), int(days * active_ratio))
            
            # Lấy bài hát yêu thích của user
            try:
                fav_songs = list(user.favorite_songs.all())
                
                # Tạo một pool bài hát yêu thích có trọng số để tăng khả năng nghe lại
                favorite_pool = []
                for song in fav_songs:
                    # Thêm mỗi bài yêu thích nhiều lần để tăng tỷ lệ được chọn
                    weight = random.randint(3, 10)  # Bài hát yêu thích được nghe lại 3-10 lần
                    favorite_pool.extend([(song, weight)] * weight)
                    
                if not favorite_pool:
                    # Nếu không có bài yêu thích, chọn ngẫu nhiên một số bài làm yêu thích
                    num_random_favs = random.randint(1, min(5, len(songs)))
                    random_favs = random.sample(songs, num_random_favs)
                    for song in random_favs:
                        weight = random.randint(2, 5)
                        favorite_pool.extend([(song, weight)] * weight)
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Lỗi khi lấy bài hát yêu thích: {e}"))
                favorite_pool = []
                
                # Chọn ngẫu nhiên một số bài làm yêu thích
                num_random_favs = random.randint(1, min(5, len(songs)))
                random_favs = random.sample(songs, num_random_favs)
                for song in random_favs:
                    weight = random.randint(2, 5)
                    favorite_pool.extend([(song, weight)] * weight)
            
            # Duyệt qua từng ngày và tạo lịch sử nghe
            for day_index in range(days):
                if day_index not in active_days:
                    continue
                
                current_day = now - timedelta(days=days-day_index-1)
                daily_plays = int(base_daily_plays * day_weights[day_index])
                
                # Phân bổ số lượt nghe giữa bài yêu thích và bài khác
                fav_ratio = 0.6  # 60% nghe bài yêu thích, 40% khám phá bài mới
                fav_plays = int(daily_plays * fav_ratio)
                other_plays = daily_plays - fav_plays
                
                # Nghe bài yêu thích
                for _ in range(fav_plays):
                    if favorite_pool:
                        song, weight = random.choice(favorite_pool)
                    else:
                        song = random.choice(songs)
                    
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
                
                # Khám phá bài hát mới
                for _ in range(other_plays):
                    song = random.choice(songs)
                    
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
                    
                # Thêm một số lượt nghe lặp lại bài hát trong cùng ngày - để kiểm tra chức năng lọc bỏ trùng lặp
                if user in active_users and random.random() < 0.8:  # 80% khả năng nghe lặp lại bài hát
                    # Chọn 1-3 bài hát để nghe lặp lại
                    repeat_count = random.randint(1, 3)
                    repeat_songs = []
                    
                    if favorite_pool:
                        for _ in range(repeat_count):
                            song, _ = random.choice(favorite_pool)
                            repeat_songs.append(song)
                    else:
                        repeat_songs = random.sample(songs, min(repeat_count, len(songs)))
                    
                    # Mỗi bài nghe lặp lại 2-5 lần
                    for song in repeat_songs:
                        repeat_times = random.randint(2, 5)
                        
                        for _ in range(repeat_times):
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
        
        # Cập nhật số lượt phát cho các bài hát
        self.stdout.write(self.style.WARNING('Đang cập nhật số lượt phát cho bài hát...'))
        for song in songs:
            play_count = SongPlayHistory.objects.filter(song=song).count()
            song.play_count = play_count
            song.save()
        
        self.stdout.write(self.style.SUCCESS(f'Đã tạo thành công {total_plays} lượt nghe nhạc trong {days} ngày!')) 