import os
import django
import random
from datetime import datetime, timedelta

# Thiết lập Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_chat.settings')
django.setup()

from django.utils import timezone
from django.db.models import Count, F, Q
from music.models import Song, Album, Artist, Genre, Playlist
from django.contrib.auth import get_user_model
from utils.pylance_helpers import safe_get_related_field

User = get_user_model()

class RealisticPlaylistGenerator:
    """
    Tạo playlist thực tế dựa trên dữ liệu hiện có
    Áp dụng các quy tắc tự nhiên:
    - Playlist thường có chủ đề hoặc thể loại nhất quán
    - Người dùng tích cực thường có nhiều playlist hơn
    - Playlist thường có độ dài hợp lý
    """
    def __init__(self):
        self.users = list(User.objects.all())
        self.songs = list(Song.objects.all())
        self.all_genres = list(set(song.genre for song in self.songs if song.genre))
        self.now = timezone.now()
        
        # Chia người dùng thành nhóm theo mức độ hoạt động
        random.shuffle(self.users)
        user_count = len(self.users)
        
        # Xử lý trường hợp ít người dùng
        if user_count == 0:
            print("CẢNH BÁO: Không có người dùng nào trong hệ thống. Không thể tạo playlist.")
            self.active_users = []
            self.moderate_users = []
            self.casual_users = []
        elif user_count == 1:
            # Nếu chỉ có 1 người dùng, coi họ là người dùng tích cực
            print("CẢNH BÁO: Chỉ có 1 người dùng trong hệ thống.")
            self.active_users = self.users.copy()
            self.moderate_users = self.users.copy()
            self.casual_users = []
        elif user_count < 5:
            # Nếu ít người dùng, chia đều vào các nhóm
            print(f"CẢNH BÁO: Chỉ có {user_count} người dùng trong hệ thống.")
            self.active_users = self.users[:1]  # Ít nhất 1 người dùng tích cực
            self.moderate_users = self.users[1:2] if user_count > 1 else []
            self.casual_users = self.users[2:] if user_count > 2 else []
        else:
            # Phân chia bình thường nếu đủ người dùng
            self.active_users = self.users[:int(user_count * 0.2)]  # 20% người dùng rất tích cực
            self.moderate_users = self.users[int(user_count * 0.2):int(user_count * 0.6)]  # 40% người dùng bình thường
            self.casual_users = self.users[int(user_count * 0.6):]  # 40% người dùng thỉnh thoảng
        
        # Tên mẫu cho playlist
        self.playlist_prefixes = [
            "Tuyển tập", "Best of", "Top", "Favorite", "My", "Ultimate", 
            "Essential", "Perfect", "Classic", "Modern", "Chill", "Party",
            "Relax", "Workout", "Focus", "Study", "Drive", "Travel"
        ]
        
        self.playlist_descriptions = [
            "Những bài hát hay nhất của thể loại này",
            "Playlist để thư giãn và tận hưởng",
            "Tuyển tập các ca khúc nổi tiếng",
            "Nhạc hay tôi thích nghe mỗi ngày",
            "Những giai điệu làm tôi nhớ mãi",
            "Playlist này sẽ làm bạn yêu thích ngay từ lần nghe đầu tiên",
            "Tuyển chọn những bài hát hay nhất",
            "Âm nhạc là liều thuốc cho tâm hồn",
            "Dành cho những phút giây thư giãn",
            "Playlist hoàn hảo cho mọi thời điểm"
        ]
        
        # Báo cáo
        print(f"Đã tìm thấy {len(self.users)} người dùng")
        print(f"Đã tìm thấy {len(self.songs)} bài hát")
        print(f"Đã tìm thấy {len(self.all_genres)} thể loại")
    
    def run(self):
        """Chạy quá trình tạo playlist thực tế"""
        print("Bắt đầu tạo playlist thực tế...")
        self.generate_genre_playlists()
        self.generate_mood_playlists()
        self.generate_artist_playlists()
        self.generate_personal_playlists()
        self.generate_playlist_follows()
        print("Hoàn thành tạo playlist thực tế!")
    
    def generate_genre_playlists(self):
        """Tạo playlist theo thể loại"""
        print("Tạo playlist theo thể loại...")
        
        # Kiểm tra xem có đủ người dùng không
        if not self.users:
            print("Không có người dùng để tạo playlist theo thể loại.")
            return
            
        genre_playlist_count = 0
        
        # Mỗi thể loại sẽ có 2-3 playlist
        for genre in self.all_genres:
            if not genre:  # Bỏ qua nếu genre rỗng
                continue
                
            # Lọc bài hát theo thể loại
            genre_songs = [song for song in self.songs if song.genre == genre]
            
            if not genre_songs:
                continue
                
            # Kiểm tra xem có đủ bài hát không
            if len(genre_songs) < 5:
                print(f"Không đủ bài hát cho thể loại {genre}, bỏ qua.")
                continue
                
            # Tạo 2-3 playlist cho mỗi thể loại
            for i in range(random.randint(2, 3)):
                # Chọn người dùng tạo playlist
                if i == 0 and self.active_users:  # Playlist đầu tiên do người dùng tích cực tạo
                    user = random.choice(self.active_users)
                else:
                    user = random.choice(self.users)  # Các playlist khác ngẫu nhiên
                
                # Tạo tên playlist
                prefix = random.choice(self.playlist_prefixes)
                playlist_name = f"{prefix} {genre}"
                
                # Tạo mô tả
                description = random.choice(self.playlist_descriptions)
                
                # Quyết định có công khai hay không
                is_public = random.random() < 0.8  # 80% playlist là công khai
                
                # Chọn số lượng bài hát - đảm bảo khoảng hợp lệ
                min_songs = min(10, len(genre_songs) - 1)  # Tối thiểu số bài hát
                max_songs = min(30, len(genre_songs))      # Tối đa số bài hát
                
                if min_songs >= max_songs:
                    num_songs = max_songs  # Nếu khoảng không hợp lệ, lấy giá trị tối đa
                else:
                    num_songs = random.randint(min_songs, max_songs)
                
                selected_songs = random.sample(genre_songs, num_songs)
                
                # Tạo ngày
                days_ago = random.randint(0, 180)  # Trong 6 tháng gần đây
                created_at = self.now - timedelta(days=days_ago)
                
                # Tạo playlist
                try:
                    playlist = Playlist.objects.create(
                        name=playlist_name,
                        description=description,
                        user=user,
                        is_public=is_public,
                        created_at=created_at
                    )
                    
                    # Thêm bài hát vào playlist
                    for song in selected_songs:
                        playlist.songs.add(song)
                    
                    genre_playlist_count += 1
                except Exception as e:
                    print(f"Lỗi khi tạo playlist thể loại: {e}")
        
        print(f"Đã tạo {genre_playlist_count} playlist theo thể loại")
    
    def generate_mood_playlists(self):
        """Tạo playlist theo tâm trạng"""
        print("Tạo playlist theo tâm trạng...")
        
        # Kiểm tra xem có đủ người dùng không
        if not self.users:
            print("Không có người dùng để tạo playlist theo tâm trạng.")
            return
            
        # Kiểm tra xem có đủ bài hát không
        if len(self.songs) < 5:
            print("Không đủ bài hát để tạo playlist tâm trạng.")
            return
            
        # Định nghĩa các tâm trạng và từ khóa liên quan
        moods = {
            "Chill": ["chill", "relax", "acoustic", "calm", "soft"],
            "Party": ["dance", "edm", "remix", "club", "party"],
            "Focus": ["focus", "study", "work", "concentration", "ambient"],
            "Workout": ["gym", "workout", "running", "exercise", "training"],
            "Sad": ["sad", "ballad", "emotional", "breakup", "melancholy"],
            "Happy": ["happy", "upbeat", "cheerful", "positive", "joy"],
            "Romantic": ["love", "romantic", "couple", "valentine", "wedding"]
        }
        
        mood_playlist_count = 0
        
        # Tạo playlist cho mỗi tâm trạng
        for mood, keywords in moods.items():
            # Mỗi tâm trạng sẽ có 2-4 playlist
            for i in range(random.randint(2, 4)):
                # Chọn người dùng
                if i == 0 and self.active_users:
                    user = random.choice(self.active_users)
                else:
                    user = random.choice(self.users)
                
                # Tạo tên playlist
                if random.random() < 0.5:
                    playlist_name = f"{mood} Music"
                else:
                    playlist_name = f"{random.choice(self.playlist_prefixes)} {mood}"
                
                # Tạo mô tả
                description = random.choice(self.playlist_descriptions)
                
                # Quyết định có công khai hay không
                is_public = random.random() < 0.9  # 90% playlist tâm trạng là công khai
                
                # Chọn bài hát phù hợp với tâm trạng (giả lập đơn giản)
                # Trong thực tế sẽ dùng phân tích cảm xúc hoặc phân loại bài hát theo BPM, lời, v.v.
                # Ở đây ta chọn ngẫu nhiên từ các thể loại
                available_songs = min(100, len(self.songs))
                mood_songs = random.sample(self.songs, available_songs)
                
                # Số lượng bài hát trong playlist - đảm bảo khoảng hợp lệ
                min_songs = min(15, available_songs - 1)  # Tối thiểu số bài hát
                max_songs = min(40, available_songs)      # Tối đa số bài hát
                
                if min_songs >= max_songs:
                    num_songs = max_songs  # Nếu khoảng không hợp lệ, lấy giá trị tối đa
                else:
                    num_songs = random.randint(min_songs, max_songs)
                    
                selected_songs = random.sample(mood_songs, num_songs)
                
                # Tạo ngày
                days_ago = random.randint(0, 120)  # Trong 4 tháng gần đây
                created_at = self.now - timedelta(days=days_ago)
                
                # Tạo playlist
                try:
                    playlist = Playlist.objects.create(
                        name=playlist_name,
                        description=description,
                        user=user,
                        is_public=is_public,
                        created_at=created_at
                    )
                    
                    # Thêm bài hát vào playlist
                    for song in selected_songs:
                        playlist.songs.add(song)
                    
                    mood_playlist_count += 1
                except Exception as e:
                    print(f"Lỗi khi tạo playlist tâm trạng: {e}")
        
        print(f"Đã tạo {mood_playlist_count} playlist theo tâm trạng")
    
    def generate_artist_playlists(self):
        """Tạo playlist theo nghệ sĩ"""
        print("Tạo playlist theo nghệ sĩ...")
        
        # Kiểm tra xem có đủ người dùng không
        if not self.users:
            print("Không có người dùng để tạo playlist theo nghệ sĩ.")
            return
            
        # Lấy danh sách nghệ sĩ có ít nhất 3 bài hát
        artist_counts = {}
        for song in self.songs:
            if song.artist:
                artist_counts[song.artist] = artist_counts.get(song.artist, 0) + 1
        
        # Lọc nghệ sĩ có đủ bài hát
        qualified_artists = [artist for artist, count in artist_counts.items() if count >= 3]
        
        # Nếu không đủ nghệ sĩ, bỏ qua
        if not qualified_artists:
            print("Không đủ nghệ sĩ để tạo playlist")
            return
        
        # Chọn ngẫu nhiên 10 nghệ sĩ hoặc ít hơn
        num_artists = min(10, len(qualified_artists))
        selected_artists = random.sample(qualified_artists, num_artists)
        
        artist_playlist_count = 0
        
        # Tạo playlist cho mỗi nghệ sĩ đã chọn
        for artist in selected_artists:
            # Lọc bài hát theo nghệ sĩ
            artist_songs = [song for song in self.songs if song.artist == artist]
            
            # Nếu không đủ bài hát, bỏ qua
            if len(artist_songs) < 3:
                continue
                
            # Chọn người dùng tạo playlist
            user = random.choice(self.users)
            
            # Tạo tên playlist
            if random.random() < 0.6:
                playlist_name = f"Best of {artist}"
            else:
                playlist_name = f"{artist} - {random.choice(['Collection', 'Hits', 'Favorites', 'Essentials'])}"
            
            # Tạo mô tả
            description = f"Tuyển tập các bài hát hay nhất của {artist}"
            
            # Công khai
            is_public = True
            
            # Số lượng bài hát - đảm bảo khoảng hợp lệ
            artist_song_count = len(artist_songs)
            num_songs = min(artist_song_count, random.randint(3, artist_song_count))
            selected_songs = random.sample(artist_songs, num_songs)
            
            # Tạo ngày
            days_ago = random.randint(0, 150)
            created_at = self.now - timedelta(days=days_ago)
            
            # Tạo playlist
            try:
                playlist = Playlist.objects.create(
                    name=playlist_name,
                    description=description,
                    user=user,
                    is_public=is_public,
                    created_at=created_at
                )
                
                # Thêm bài hát vào playlist
                for song in selected_songs:
                    playlist.songs.add(song)
                
                artist_playlist_count += 1
            except Exception as e:
                print(f"Lỗi khi tạo playlist nghệ sĩ: {e}")
        
        print(f"Đã tạo {artist_playlist_count} playlist theo nghệ sĩ")
    
    def generate_personal_playlists(self):
        """Tạo playlist cá nhân cho người dùng"""
        print("Tạo playlist cá nhân...")
        
        # Kiểm tra xem có đủ người dùng không
        if not self.users:
            print("Không có người dùng để tạo playlist cá nhân.")
            return
            
        # Kiểm tra xem có đủ bài hát không
        if len(self.songs) < 5:
            print("Không đủ bài hát để tạo playlist cá nhân.")
            return
            
        personal_playlist_count = 0
        
        for user in self.users:
            # Số lượng playlist dựa trên mức độ hoạt động
            if user in self.active_users:
                num_playlists = random.randint(2, 5)
            elif user in self.moderate_users:
                num_playlists = random.randint(1, 3)
            else:
                num_playlists = random.randint(0, 2)
            
            # Thử lấy bài hát yêu thích của user
            fav_songs = []
            user_favorites = safe_get_related_field(user, 'favorite_songs')
            if user_favorites:
                try:
                    fav_songs = list(user_favorites.all())
                except:
                    fav_songs = []
            
            # Tạo playlist cá nhân
            for i in range(num_playlists):
                # Tạo tên playlist
                playlist_names = [
                    f"Playlist của {user.username}",
                    f"Nhạc {random.choice(['Chill', 'Party', 'Workout', 'Study', 'Sleep', 'Travel'])}",
                    f"Mix {random.choice(['#1', '#2', '#3', 'Daily', 'Weekly'])}",
                    f"Top Picks",
                    f"Những bài hát yêu thích",
                    f"Playlist {random.randint(1, 10)}"
                ]
                playlist_name = random.choice(playlist_names)
                
                # Tạo mô tả
                descriptions = [
                    "Những bài hát tôi thích",
                    "Playlist cá nhân",
                    "Nhạc để thư giãn sau ngày dài",
                    "Các bài hát tôi thường nghe",
                    "Nhạc tâm trạng",
                    "Nhạc để chill cuối tuần"
                ]
                description = random.choice(descriptions)
                
                # Xác định tính riêng tư
                is_public = random.random() < 0.6  # 60% playlist cá nhân là công khai
                
                # Chọn bài hát
                selected_songs = []
                if fav_songs and random.random() < 0.7 and len(fav_songs) >= 2:
                    # 70% trường hợp ưu tiên bài hát yêu thích
                    fav_count = len(fav_songs)
                    num_fav = min(fav_count, random.randint(2, fav_count))
                    selected_songs = random.sample(fav_songs, num_fav)
                    
                    # Bổ sung thêm bài hát ngẫu nhiên
                    remaining_songs = [s for s in self.songs if s not in selected_songs]
                    if remaining_songs:  # Kiểm tra xem còn bài hát nào không
                        additional = random.randint(0, 15)
                        if additional > 0:
                            additional = min(additional, len(remaining_songs))
                            selected_songs.extend(random.sample(remaining_songs, additional))
                else:
                    # Chọn hoàn toàn ngẫu nhiên
                    song_count = len(self.songs)
                    num_songs = min(song_count, random.randint(5, min(30, song_count)))
                    selected_songs = random.sample(self.songs, num_songs)
                    
                # Nếu không có bài hát được chọn, bỏ qua
                if not selected_songs:
                    continue
                    
                # Tạo ngày
                days_ago = random.randint(0, 90)
                created_at = self.now - timedelta(days=days_ago)
                
                # Tạo playlist
                try:
                    playlist = Playlist.objects.create(
                        name=playlist_name,
                        description=description,
                        user=user,
                        is_public=is_public,
                        created_at=created_at
                    )
                    
                    # Thêm bài hát vào playlist
                    for song in selected_songs:
                        playlist.songs.add(song)
                    
                    personal_playlist_count += 1
                except Exception as e:
                    print(f"Lỗi khi tạo playlist cá nhân: {e}")
        
        print(f"Đã tạo {personal_playlist_count} playlist cá nhân")
    
    def generate_playlist_follows(self):
        """Tạo lượt theo dõi playlist"""
        print("Tạo lượt theo dõi playlist...")
        
        # Kiểm tra xem có đủ người dùng không
        if not self.users:
            print("Không có người dùng để tạo lượt theo dõi playlist.")
            return
            
        # Lấy tất cả playlist công khai
        public_playlists = list(Playlist.objects.filter(is_public=True))
        
        if not public_playlists:
            print("Không có playlist công khai để tạo lượt theo dõi.")
            return
            
        # Lượt theo dõi theo mức độ người dùng
        follow_count = 0
        
        for user in self.users:
            # Số lượng playlist sẽ theo dõi
            if user in self.active_users:
                num_follows = random.randint(5, 15)
            elif user in self.moderate_users:
                num_follows = random.randint(2, 8)
            else:
                num_follows = random.randint(0, 4)
            
            # Chọn ngẫu nhiên playlist để theo dõi
            if public_playlists and num_follows > 0:
                to_follow = random.sample(public_playlists, min(num_follows, len(public_playlists)))
                
                for playlist in to_follow:
                    # Bỏ qua playlist của chính mình (đã tự động follow)
                    if playlist.user == user:
                        continue
                    
                    try:
                        # Thêm vào danh sách theo dõi - sử dụng helper
                        user_followed_playlists = safe_get_related_field(user, 'followed_playlists')
                        if user_followed_playlists:
                            user_followed_playlists.add(playlist)
                            follow_count += 1
                    except Exception as e:
                        print(f"Lỗi khi thêm follow playlist: {e}")
        
        print(f"Đã tạo {follow_count} lượt theo dõi playlist")

# Chạy script nếu thực thi trực tiếp
if __name__ == "__main__":
    generator = RealisticPlaylistGenerator()
    generator.run() 