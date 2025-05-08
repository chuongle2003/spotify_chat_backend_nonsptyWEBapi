from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Song
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import os

User = get_user_model()

class AdminSongUpdateTest(TestCase):
    def setUp(self):
        # Tạo admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword123'
        )
        
        # Tạo một regular user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpassword123'
        )
        
        # Tạo một bài hát mẫu
        # Tạo ảnh bìa mẫu
        image = BytesIO()
        Image.new('RGB', (100, 100)).save(image, 'JPEG')
        image.seek(0)
        cover_image = SimpleUploadedFile("cover.jpg", image.getvalue(), content_type="image/jpeg")
        
        # Tạo audio file mẫu
        audio = tempfile.NamedTemporaryFile(suffix='.mp3')
        audio.write(b'x' * 10000)  # Tạo dữ liệu giả
        audio.seek(0)
        audio_file = SimpleUploadedFile("song.mp3", audio.read(), content_type="audio/mpeg")
        
        # Tạo bài hát với admin là người upload
        self.song = Song.objects.create(
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            genre="Rock",
            duration=180,  # 3 phút
            lyrics="Test lyrics for the song",
            is_approved=True,
            uploaded_by=self.admin_user,
            audio_file=audio_file,
            cover_image=cover_image
        )
        
        # URL cập nhật bài hát
        self.url = f'/api/v1/music/admin/songs/{self.song.id}/'
        
        # Tạo client
        self.client = Client()
        
    def test_update_song_with_files(self):
        """Test cập nhật bài hát với các trường dữ liệu và files"""
        # Đăng nhập với admin
        self.client.login(username='admin', password='adminpassword123')
        
        # Tạo ảnh bìa mới
        new_image = BytesIO()
        Image.new('RGB', (200, 200), color='red').save(new_image, 'JPEG')
        new_image.seek(0)
        new_cover = SimpleUploadedFile("new_cover.jpg", new_image.getvalue(), content_type="image/jpeg")
        
        # Tạo audio file mới
        new_audio = tempfile.NamedTemporaryFile(suffix='.mp3')
        new_audio.write(b'y' * 20000)  # Tạo dữ liệu giả khác với file cũ
        new_audio.seek(0)
        new_audio_file = SimpleUploadedFile("new_song.mp3", new_audio.read(), content_type="audio/mpeg")
        
        # Dữ liệu cập nhật
        data = {
            'title': 'Updated Song Title',
            'artist': 'Updated Artist',
            'genre': 'Pop',
            'lyrics': 'Updated lyrics for the song',
            'is_approved': False
        }
        
        # Thực hiện PATCH request với cả dữ liệu và files
        response = self.client.patch(
            self.url, 
            data=data,
            HTTP_CONTENT_TYPE='application/json'
        )
        
        # Kiểm tra response status
        self.assertEqual(response.status_code, 200)
        
        # Kiểm tra dữ liệu đã được cập nhật
        updated_song = Song.objects.get(id=self.song.id)
        self.assertEqual(updated_song.title, 'Updated Song Title')
        self.assertEqual(updated_song.artist, 'Updated Artist')
        self.assertEqual(updated_song.genre, 'Pop')
        self.assertEqual(updated_song.lyrics, 'Updated lyrics for the song')
        self.assertEqual(updated_song.is_approved, False)
        
        # Test cập nhật chỉ với file
        response_file = self.client.patch(
            self.url,
            {'cover_image': new_cover, 'audio_file': new_audio_file},
            format='multipart'
        )
        
        # Kiểm tra response status
        self.assertEqual(response_file.status_code, 200)
        
        # Làm mới đối tượng từ database
        updated_song = Song.objects.get(id=self.song.id)
        
        # Lưu ý: Để kiểm tra files thì cần so sánh nội dung hoặc kích thước
        # Trong unit test ta có thể kiểm tra xem trường có được cập nhật không
        self.assertTrue(updated_song.cover_image)
        self.assertTrue(updated_song.audio_file)
        
    def test_unauthorized_update(self):
        """Test không cho phép user thường cập nhật bài hát qua API admin"""
        # Đăng nhập với user thường
        self.client.login(username='regularuser', password='regularpassword123')
        
        # Dữ liệu cập nhật
        data = {
            'title': 'Malicious Update',
        }
        
        # Thực hiện PATCH request
        response = self.client.patch(self.url, data=data)
        
        # Kiểm tra response status (phải bị từ chối - 403 hoặc 401)
        self.assertIn(response.status_code, [401, 403])
        
        # Kiểm tra dữ liệu không bị thay đổi
        unchanged_song = Song.objects.get(id=self.song.id)
        self.assertEqual(unchanged_song.title, 'Test Song')  # Vẫn giữ giá trị cũ
        
    def tearDown(self):
        # Xóa các file đã tạo trong quá trình test
        if self.song.cover_image:
            if os.path.isfile(self.song.cover_image.path):
                os.remove(self.song.cover_image.path)
                
        if self.song.audio_file:
            if os.path.isfile(self.song.audio_file.path):
                os.remove(self.song.audio_file.path)

class AdminMediaUploadTest(TestCase):
    def setUp(self):
        # Tạo admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword123'
        )
        
        # Tạo một regular user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpassword123'
        )
        
        # Tạo các đối tượng mẫu cho từng model
        # Tạo ảnh mẫu
        image = BytesIO()
        Image.new('RGB', (100, 100)).save(image, 'JPEG')
        image.seek(0)
        cover_image = SimpleUploadedFile("cover.jpg", image.getvalue(), content_type="image/jpeg")
        
        # 1. Tạo Album mẫu
        from .models import Album
        self.album = Album.objects.create(
            title="Test Album",
            artist="Test Artist",
            release_date="2023-01-01",
            description="Test album description",
            cover_image=cover_image
        )
        
        # 2. Tạo Artist mẫu
        from .models import Artist
        self.artist = Artist.objects.create(
            name="Test Artist",
            bio="Test artist bio",
            image=cover_image
        )
        
        # 3. Tạo Genre mẫu
        from .models import Genre
        self.genre = Genre.objects.create(
            name="Test Genre",
            description="Test genre description",
            image=cover_image
        )
        
        # 4. Tạo Playlist mẫu
        from .models import Playlist
        self.playlist = Playlist.objects.create(
            name="Test Playlist",
            description="Test playlist description",
            is_public=True,
            user=self.admin_user,
            cover_image=cover_image
        )
        
        # Tạo client
        self.client = Client()
        
    def test_album_update_cover_image(self):
        """Test cập nhật ảnh bìa cho album"""
        # Đăng nhập với admin
        self.client.login(username='admin', password='adminpassword123')
        
        # Tạo ảnh mới
        new_image = BytesIO()
        Image.new('RGB', (200, 200), color='red').save(new_image, 'JPEG')
        new_image.seek(0)
        new_cover = SimpleUploadedFile("new_album_cover.jpg", new_image.getvalue(), content_type="image/jpeg")
        
        # URL cập nhật album
        url = f'/api/v1/music/admin/albums/{self.album.id}/'
        
        # Thực hiện PATCH request
        response = self.client.patch(
            url,
            {'title': 'Updated Album Title', 'cover_image': new_cover},
            format='multipart'
        )
        
        # Kiểm tra response status
        self.assertEqual(response.status_code, 200)
        
        # Refresh từ database
        from .models import Album
        updated_album = Album.objects.get(id=self.album.id)
        
        # Kiểm tra metadata và file đã được cập nhật
        self.assertEqual(updated_album.title, 'Updated Album Title')
        self.assertTrue(updated_album.cover_image)
        self.assertNotEqual(str(self.album.cover_image), str(updated_album.cover_image))
    
    def test_artist_update_image(self):
        """Test cập nhật ảnh cho nghệ sĩ"""
        # Đăng nhập với admin
        self.client.login(username='admin', password='adminpassword123')
        
        # Tạo ảnh mới
        new_image = BytesIO()
        Image.new('RGB', (200, 200), color='blue').save(new_image, 'JPEG')
        new_image.seek(0)
        new_artist_image = SimpleUploadedFile("new_artist_image.jpg", new_image.getvalue(), content_type="image/jpeg")
        
        # URL cập nhật nghệ sĩ
        url = f'/api/v1/music/admin/artists/{self.artist.id}/'
        
        # Thực hiện PATCH request
        response = self.client.patch(
            url,
            {'name': 'Updated Artist Name', 'image': new_artist_image},
            format='multipart'
        )
        
        # Kiểm tra response status
        self.assertEqual(response.status_code, 200)
        
        # Refresh từ database
        from .models import Artist
        updated_artist = Artist.objects.get(id=self.artist.id)
        
        # Kiểm tra metadata và file đã được cập nhật
        self.assertEqual(updated_artist.name, 'Updated Artist Name')
        self.assertTrue(updated_artist.image)
        self.assertNotEqual(str(self.artist.image), str(updated_artist.image))
    
    def test_genre_update_image(self):
        """Test cập nhật ảnh cho thể loại"""
        # Đăng nhập với admin
        self.client.login(username='admin', password='adminpassword123')
        
        # Tạo ảnh mới
        new_image = BytesIO()
        Image.new('RGB', (200, 200), color='green').save(new_image, 'JPEG')
        new_image.seek(0)
        new_genre_image = SimpleUploadedFile("new_genre_image.jpg", new_image.getvalue(), content_type="image/jpeg")
        
        # URL cập nhật thể loại
        url = f'/api/v1/music/admin/genres/{self.genre.id}/'
        
        # Thực hiện PATCH request
        response = self.client.patch(
            url,
            {'name': 'Updated Genre Name', 'image': new_genre_image},
            format='multipart'
        )
        
        # Kiểm tra response status
        self.assertEqual(response.status_code, 200)
        
        # Refresh từ database
        from .models import Genre
        updated_genre = Genre.objects.get(id=self.genre.id)
        
        # Kiểm tra metadata và file đã được cập nhật
        self.assertEqual(updated_genre.name, 'Updated Genre Name')
        self.assertTrue(updated_genre.image)
        self.assertNotEqual(str(self.genre.image), str(updated_genre.image))
    
    def test_playlist_update_cover_image(self):
        """Test cập nhật ảnh bìa cho playlist"""
        # Đăng nhập với admin
        self.client.login(username='admin', password='adminpassword123')
        
        # Tạo ảnh mới
        new_image = BytesIO()
        Image.new('RGB', (200, 200), color='yellow').save(new_image, 'JPEG')
        new_image.seek(0)
        new_playlist_cover = SimpleUploadedFile("new_playlist_cover.jpg", new_image.getvalue(), content_type="image/jpeg")
        
        # URL cập nhật playlist
        url = f'/api/v1/music/admin/playlists/{self.playlist.id}/'
        
        # Thực hiện PATCH request
        response = self.client.patch(
            url,
            {'name': 'Updated Playlist Name', 'cover_image': new_playlist_cover},
            format='multipart'
        )
        
        # Kiểm tra response status
        self.assertEqual(response.status_code, 200)
        
        # Refresh từ database
        from .models import Playlist
        updated_playlist = Playlist.objects.get(id=self.playlist.id)
        
        # Kiểm tra metadata và file đã được cập nhật
        self.assertEqual(updated_playlist.name, 'Updated Playlist Name')
        self.assertTrue(updated_playlist.cover_image)
        self.assertNotEqual(str(self.playlist.cover_image), str(updated_playlist.cover_image))
    
    def test_unauthorized_media_upload(self):
        """Test không cho phép user thường cập nhật thông qua API admin"""
        # Đăng nhập với user thường
        self.client.login(username='regularuser', password='regularpassword123')
        
        # Tạo ảnh mới
        new_image = BytesIO()
        Image.new('RGB', (200, 200), color='purple').save(new_image, 'JPEG')
        new_image.seek(0)
        new_cover = SimpleUploadedFile("unauthorized_image.jpg", new_image.getvalue(), content_type="image/jpeg")
        
        # Thử cập nhật album
        url = f'/api/v1/music/admin/albums/{self.album.id}/'
        response = self.client.patch(
            url,
            {'title': 'Unauthorized Update', 'cover_image': new_cover},
            format='multipart'
        )
        
        # Kiểm tra response status (phải bị từ chối - 403 hoặc 401)
        self.assertIn(response.status_code, [401, 403])
    
    def tearDown(self):
        # Xóa các file đã tạo trong quá trình test
        # Album
        if self.album.cover_image:
            if os.path.isfile(self.album.cover_image.path):
                os.remove(self.album.cover_image.path)
        
        # Artist
        if self.artist.image:
            if os.path.isfile(self.artist.image.path):
                os.remove(self.artist.image.path)
        
        # Genre
        if self.genre.image:
            if os.path.isfile(self.genre.image.path):
                os.remove(self.genre.image.path)
        
        # Playlist
        if self.playlist.cover_image:
            if os.path.isfile(self.playlist.cover_image.path):
                os.remove(self.playlist.cover_image.path)
