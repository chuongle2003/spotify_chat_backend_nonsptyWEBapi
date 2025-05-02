from django.core.management.base import BaseCommand
from django.db.models import Count
from music.models import Song, Artist
from django.core.files import File
from pathlib import Path
import random
import os
import requests
from io import BytesIO
from PIL import Image
from django.conf import settings
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tạo dữ liệu nghệ sĩ từ bài hát có sẵn'

    def add_arguments(self, parser):
        parser.add_argument('--sample_image_dir', type=str, help='Thư mục chứa ảnh mẫu cho nghệ sĩ', default='sample_images/artists')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Bắt đầu tạo dữ liệu nghệ sĩ...'))
        sample_image_dir = options.get('sample_image_dir')
        
        # Lấy danh sách tất cả nghệ sĩ từ bài hát
        artists_data = Song.objects.values('artist').annotate(
            song_count=Count('artist')
        ).order_by('-song_count')
        
        # Đảm bảo thư mục media/artist_images tồn tại
        artist_image_dir = Path(settings.MEDIA_ROOT) / 'artist_images'
        artist_image_dir.mkdir(parents=True, exist_ok=True)
        
        # Danh sách ảnh mẫu
        sample_images: List[str] = []
        if sample_image_dir and os.path.exists(sample_image_dir):
            sample_images = [
                f for f in os.listdir(sample_image_dir) 
                if os.path.isfile(os.path.join(str(sample_image_dir), f)) 
                and f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
        
        artists_created = 0
        artists_skipped = 0
        
        for artist_info in artists_data:
            artist_name = artist_info['artist']
            if not artist_name or artist_name.strip() == '':
                continue
                
            # Kiểm tra xem nghệ sĩ đã tồn tại chưa
            if Artist.objects.filter(name=artist_name).exists():
                self.stdout.write(f'Nghệ sĩ {artist_name} đã tồn tại, bỏ qua')
                artists_skipped += 1
                continue
            
            # Tạo bio mẫu cho nghệ sĩ
            bio = self._generate_bio(artist_name, artist_info['song_count'])
            
            # Tạo nghệ sĩ mới
            artist = Artist(
                name=artist_name,
                bio=bio
            )
            
            # Lưu nghệ sĩ trước để lấy ID
            artist.save()
            
            # Gắn ảnh cho nghệ sĩ
            if sample_images:
                try:
                    image_path = os.path.join(str(sample_image_dir), random.choice(sample_images))
                    with open(image_path, 'rb') as img_file:
                        artist.image.save(
                            f'{artist_name.replace(" ", "_")}.jpg',
                            File(img_file),
                            save=True
                        )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Lỗi khi thêm ảnh cho nghệ sĩ {artist_name}: {str(e)}'))
            
            artists_created += 1
            self.stdout.write(self.style.SUCCESS(f'Đã tạo nghệ sĩ: {artist_name} với {artist_info["song_count"]} bài hát'))
        
        self.stdout.write(self.style.SUCCESS(
            f'Hoàn thành! Đã tạo {artists_created} nghệ sĩ mới, bỏ qua {artists_skipped} nghệ sĩ đã tồn tại')
        )

    def _generate_bio(self, artist_name, song_count):
        """Tạo tiểu sử ngẫu nhiên cho nghệ sĩ"""
        intros = [
            f"{artist_name} là một nghệ sĩ tài năng trong làng nhạc",
            f"Nổi tiếng với phong cách độc đáo, {artist_name} đã chinh phục nhiều người nghe",
            f"{artist_name} bắt đầu sự nghiệp âm nhạc từ rất sớm và nhanh chóng gặt hái thành công",
            f"Với giọng hát đầy cảm xúc, {artist_name} đã trở thành một hiện tượng âm nhạc",
            f"{artist_name} được biết đến là một nghệ sĩ đa tài trong làng nhạc"
        ]
        
        middles = [
            f"đã phát hành {song_count} bài hát nổi tiếng",
            f"có {song_count} tác phẩm được yêu thích",
            f"sở hữu bộ sưu tập âm nhạc với {song_count} bài hát đặc sắc",
            f"đã sáng tác và trình diễn {song_count} ca khúc ấn tượng",
            f"được khán giả biết đến với {song_count} sáng tác đầy cảm xúc"
        ]
        
        endings = [
            "và tiếp tục là một trong những nghệ sĩ được yêu thích nhất hiện nay.",
            "mang đến cho người nghe những trải nghiệm âm nhạc tuyệt vời.",
            "luôn nỗ lực sáng tạo những tác phẩm chất lượng cho người hâm mộ.",
            "với phong cách âm nhạc độc đáo không thể nhầm lẫn.",
            "và đang tiếp tục khẳng định vị trí của mình trong nền âm nhạc hiện đại."
        ]
        
        return f"{random.choice(intros)} {random.choice(middles)} {random.choice(endings)}" 