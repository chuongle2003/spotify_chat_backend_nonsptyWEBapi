from django.core.management.base import BaseCommand
from music.models import Playlist, Song
from django.contrib.auth import get_user_model
from django.conf import settings
import os
import random
from datetime import datetime
from django.utils import timezone
from django.db.models import Q, Count

User = get_user_model()

class Command(BaseCommand):
    help = 'Xóa tất cả playlist hiện tại và tạo playlist mới với thông tin đầy đủ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-existing',
            action='store_true',
            help='Không xóa dữ liệu playlist cũ trước khi tạo mới'
        )
        
        parser.add_argument(
            '--playlists-per-user',
            type=int,
            default=3,
            help='Số lượng playlist tạo cho mỗi người dùng'
        )
        
        parser.add_argument(
            '--min-songs',
            type=int,
            default=5,
            help='Số lượng bài hát tối thiểu trong mỗi playlist'
        )
        
        parser.add_argument(
            '--max-songs',
            type=int,
            default=15,
            help='Số lượng bài hát tối đa trong mỗi playlist'
        )

    def handle(self, *args, **options):
        keep_existing = options['keep_existing']
        playlists_per_user = options['playlists_per_user']
        min_songs = options['min_songs']
        max_songs = options['max_songs']
        
        # Lấy tất cả người dùng và bài hát
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR('Không tìm thấy người dùng nào. Vui lòng tạo dữ liệu người dùng trước.'))
            return
            
        songs = list(Song.objects.all())
        if not songs:
            self.stdout.write(self.style.ERROR('Không tìm thấy bài hát nào. Vui lòng tạo dữ liệu bài hát trước.'))
            return
        
        # Báo cáo thông tin
        self.stdout.write(f"Đã tìm thấy {len(users)} người dùng")
        self.stdout.write(f"Đã tìm thấy {len(songs)} bài hát")
        
        if not keep_existing:
            self.stdout.write(self.style.WARNING('Đang xóa tất cả playlist cũ...'))
            Playlist.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Đã xóa tất cả playlist cũ!'))
        
        # Tạo danh sách playlist mẫu
        playlist_templates = [
            {
                'name': 'Nhạc Chill Cuối Tuần',
                'description': 'Những bài hát nhẹ nhàng, thư giãn cho cuối tuần',
                'is_public': True,
                'genre_focus': ['Nhạc Trẻ', 'Ballad']
            },
            {
                'name': 'Rap Việt Tuyển Chọn',
                'description': 'Tuyển tập những bài Rap Việt hay nhất',
                'is_public': True,
                'genre_focus': ['Nhạc Rap', 'Hip Hop']
            },
            {
                'name': 'Acoustic Cover Hay',
                'description': 'Những bản acoustic cover nhẹ nhàng, sâu lắng',
                'is_public': False,  # Đặt là private
                'genre_focus': ['Acoustic', 'Cover', 'Nhạc Trẻ']
            },
            {
                'name': 'Nhạc Trịnh Công Sơn',
                'description': 'Tuyển tập nhạc Trịnh Công Sơn hay nhất',
                'is_public': True,
                'genre_focus': ['Nhạc Trữ Tình', 'Nhạc Không Lời']
            },
            {
                'name': 'Workout Motivation',
                'description': 'Âm nhạc sôi động cho buổi tập luyện',
                'is_public': True,
                'genre_focus': ['EDM', 'Remix', 'Nhạc Rap']
            },
            {
                'name': 'Nhạc Nghe Khi Làm Việc',
                'description': 'Tăng hiệu suất làm việc với danh sách này',
                'is_public': True,
                'genre_focus': ['Nhạc Không Lời', 'Lo-fi']
            },
            {
                'name': 'Nhạc Buồn',
                'description': 'Nhạc buồn cho ngày mưa',
                'is_public': False,  # Đặt là private
                'genre_focus': ['Ballad', 'Nhạc Trữ Tình']
            },
            {
                'name': 'Top hits 2025',
                'description': 'Những bài hát được nghe nhiều nhất năm 2025',
                'is_public': True,
                'genre_focus': ['Nhạc Trẻ', 'Nhạc Rap', 'EDM']
            },
            {
                'name': 'Playlist Cá Nhân',
                'description': 'Nhạc yêu thích của tôi',
                'is_public': False,  # Luôn đặt playlist cá nhân là private
                'genre_focus': []  # Không có thể loại cụ thể
            },
            {
                'name': 'Drive Playlist',
                'description': 'Nhạc nghe khi lái xe',
                'is_public': False,  # Đặt là private
                'genre_focus': ['Nhạc Trẻ', 'Nhạc Rap']
            },
        ]
        
        # Khởi tạo biến theo dõi số lượng playlist đã tạo
        total_playlists = 0
        total_songs_added = 0
        
        # Tạo playlist cho mỗi người dùng
        for user in users:
            # Chọn template ngẫu nhiên cho mỗi người dùng
            chosen_templates = random.sample(playlist_templates, min(playlists_per_user, len(playlist_templates)))
            
            for i, template in enumerate(chosen_templates):
                # Tạo tên playlist duy nhất nếu cần
                playlist_name = f"{template['name']}"
                if i > 0:
                    playlist_name = f"{template['name']} #{i+1}"
                
                # Tạo playlist mới
                playlist = Playlist.objects.create(
                    name=playlist_name,
                    description=template['description'],
                    is_public=template['is_public'],
                    user=user,
                )
                
                # Lọc bài hát theo genre_focus nếu có
                filtered_songs = songs
                if template['genre_focus']:
                    genre_filters = Q()
                    for genre in template['genre_focus']:
                        genre_filters |= Q(genre__icontains=genre)
                    
                    # Lọc bài hát theo thể loại
                    genre_songs = [s for s in songs if any(genre.lower() in s.genre.lower() for genre in template['genre_focus'])]
                    
                    # Nếu có đủ bài hát theo thể loại
                    if len(genre_songs) >= min_songs:
                        filtered_songs = genre_songs
                
                # Xác định số lượng bài hát để thêm
                num_songs = random.randint(min_songs, min(max_songs, len(filtered_songs)))
                
                # Chọn bài hát ngẫu nhiên
                selected_songs = random.sample(filtered_songs, num_songs)
                
                # Thêm bài hát vào playlist
                for song in selected_songs:
                    # Đảm bảo bài hát có đầy đủ thông tin
                    if not song.audio_file:
                        self.stdout.write(self.style.WARNING(f"Bài hát '{song.title}' không có file audio"))
                        continue
                    
                    # Kiểm tra file audio tồn tại
                    if not os.path.exists(song.audio_file.path):
                        self.stdout.write(self.style.WARNING(f"File audio cho bài hát '{song.title}' không tồn tại"))
                        continue
                        
                    playlist.songs.add(song)
                    total_songs_added += 1
                
                # Thêm cover image nếu chưa có
                if not playlist.cover_image:
                    # Tìm bài hát có cover image
                    song_with_cover = next((s for s in selected_songs if s.cover_image), None)
                    if song_with_cover and song_with_cover.cover_image:
                        playlist.cover_image = song_with_cover.cover_image
                        playlist.save()
                        self.stdout.write(f"Đã thêm ảnh bìa từ bài hát '{song_with_cover.title}' cho playlist '{playlist.name}'")
                
                total_playlists += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Đã tạo playlist '{playlist.name}' cho người dùng {user.username} với {playlist.songs.count()} bài hát"
                ))
                
                # Tạo log truy cập
                self.stdout.write(f"Trạng thái công khai: {'Công khai' if playlist.is_public else 'Riêng tư'}")
                self.stdout.write(f"Chỉ '{user.username}' mới có thể chỉnh sửa playlist này")
                
                # Xác nhận thông tin đầy đủ
                has_audio = all(song.audio_file for song in playlist.songs.all())
                has_cover = playlist.cover_image is not None
                self.stdout.write(f"Playlist '{playlist.name}': Đầy đủ audio: {'Có' if has_audio else 'Không'}, Ảnh bìa: {'Có' if has_cover else 'Không'}")
        
        # Kiểm tra và đổi tất cả playlist cá nhân sang private nếu cần
        personal_playlists = Playlist.objects.filter(name__icontains='Cá Nhân')
        for playlist in personal_playlists:
            if playlist.is_public:
                playlist.is_public = False
                playlist.save()
                self.stdout.write(self.style.WARNING(f"Đã chuyển playlist '{playlist.name}' của {playlist.user.username} sang chế độ riêng tư"))
        
        # Tạo người dùng theo dõi playlist
        self.stdout.write(self.style.WARNING('Đang tạo người dùng theo dõi playlist...'))
        
        # Lấy tất cả playlist công khai
        public_playlists = Playlist.objects.filter(is_public=True)
        
        # Cho mỗi người dùng theo dõi ngẫu nhiên một số playlist
        for user in users:
            # Lấy playlist không phải của user hiện tại
            other_playlists = public_playlists.exclude(user=user)
            
            # Quyết định số lượng playlist để theo dõi
            num_to_follow = min(random.randint(1, 5), other_playlists.count())
            
            # Chọn ngẫu nhiên playlist để theo dõi
            if num_to_follow > 0:
                playlists_to_follow = random.sample(list(other_playlists), num_to_follow)
                
                for playlist in playlists_to_follow:
                    playlist.followers.add(user)
                    self.stdout.write(f"Người dùng {user.username} đã theo dõi playlist '{playlist.name}'")
                    # Ghi log truy cập
                    if not playlist.is_public and playlist.user != user:
                        self.stdout.write(self.style.WARNING(
                            f"Người dùng {user.username} không thể truy cập nội dung của playlist riêng tư '{playlist.name}'"
                        ))
        
        # Hiển thị thông tin tóm tắt
        self.stdout.write(self.style.SUCCESS(f"Đã tạo thành công {total_playlists} playlist với tổng cộng {total_songs_added} bài hát!"))
        self.stdout.write(self.style.SUCCESS("Đã hoàn thành việc tạo dữ liệu playlist!"))
        
        # Hiển thị thông tin quyền riêng tư
        private_count = Playlist.objects.filter(is_public=False).count()
        public_count = Playlist.objects.filter(is_public=True).count()
        self.stdout.write(self.style.SUCCESS(f"Tổng số playlist riêng tư: {private_count}"))
        self.stdout.write(self.style.SUCCESS(f"Tổng số playlist công khai: {public_count}"))
        self.stdout.write(self.style.SUCCESS("Đã thiết lập quyền riêng tư thành công!")) 