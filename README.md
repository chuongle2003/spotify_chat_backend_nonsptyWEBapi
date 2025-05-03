# Spotify Chat Backend

Ứng dụng chat với trình phát nhạc tích hợp, cho phép người dùng chia sẻ và trò chuyện về âm nhạc.

## Tính năng

### Quản lý tài khoản

- Đăng ký, đăng nhập
- Quản lý hồ sơ: cập nhật avatar, bio
- Theo dõi người dùng khác

### Quản lý nhạc

- Tải lên bài hát
- Quản lý danh sách bài hát
- Phát nhạc trực tuyến
- Xem thông tin chi tiết bài hát, lời bài hát

### Playlist

- Tạo và quản lý playlist
- Thêm/xóa bài hát từ playlist
- Theo dõi playlist của người khác

### Khám phá nhạc

- Tìm kiếm bài hát, album, playlist
- Xem bài hát xu hướng
- Nhận đề xuất bài hát dựa trên sở thích
- Duyệt theo thể loại

### Tương tác xã hội

- Đánh giá bài hát (1-5 sao)
- Bình luận về bài hát
- Yêu thích bài hát

### Chat và chia sẻ

- Nhắn tin trực tiếp với người dùng khác
- Chia sẻ bài hát/playlist qua chat
- Gửi hình ảnh, voice note, file đính kèm

## Yêu cầu hệ thống

- Python 3.8+
- Django 5.0+
- PostgreSQL 12+
- Node.js và npm (cho frontend)

## Cài đặt

1. Clone repository:

```bash
git clone https://github.com/your-username/spotify-chat-backend.git
cd spotify-chat-backend
```

2. Tạo môi trường ảo:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

3. Cài đặt các gói phụ thuộc:

```bash
pip install -r requirements.txt
```

4. Cấu hình môi trường:

   - Tạo file `.env` từ file `.env.example`
   - Cập nhật các cấu hình phù hợp với môi trường của bạn

5. Cấu hình database:

```bash
# Đăng nhập vào PostgreSQL
psql -U postgres

# Tạo database
CREATE DATABASE spotify_chat_db;

# Thoát PostgreSQL
\q
```

6. Chạy migrations:

```bash
python manage.py makemigrations accounts
python manage.py makemigrations music
python manage.py makemigrations chat
python manage.py migrate
```

7. Tạo superuser:

```bash
python manage.py createsuperuser
```

8. Tạo dữ liệu mẫu (tùy chọn):

```bash
python seed_data.py
```

9. Chạy server:

```bash
python manage.py runserver
```

10. Truy cập:
    - Admin interface: http://localhost:8000/admin/
    - API documentation: http://localhost:8000/api/schema/swagger-ui/

## Cấu trúc dự án

```
spotify_chat_backend/
├── accounts/            # Quản lý người dùng
├── music/               # Quản lý nhạc, playlist, album
├── chat/                # Hệ thống chat và tin nhắn
├── backend/             # Cấu hình Django project
├── media/               # Media files (uploads)
├── static/              # Static files
├── .env.example         # Mẫu file môi trường
├── requirements.txt     # Dependencies
├── manage.py
└── README.md
```

## API Endpoints

### Authentication

- `POST /api/token/`: Lấy access token
- `POST /api/token/refresh/`: Refresh token
- `POST /api/register/`: Đăng ký tài khoản

### Music

- `GET/POST /api/songs/`: Lấy danh sách/Tạo bài hát
- `GET/PUT/DELETE /api/songs/{id}/`: Xem/Cập nhật/Xóa bài hát
- `POST /api/songs/{id}/play/`: Ghi nhận lượt phát
- `POST /api/songs/{id}/like/`: Yêu thích bài hát
- `POST /api/upload/`: Upload bài hát mới

### Playlist

- `GET/POST /api/playlists/`: Lấy danh sách/Tạo playlist
- `GET/PUT/DELETE /api/playlists/{id}/`: Xem/Cập nhật/Xóa playlist
- `POST /api/playlists/{id}/add_song/`: Thêm bài hát vào playlist
- `POST /api/playlists/{id}/remove_song/`: Xóa bài hát khỏi playlist

### Discover

- `GET /api/search/?q={query}`: Tìm kiếm
- `GET /api/trending/`: Bài hát xu hướng
- `GET /api/recommended/`: Bài hát đề xuất

### Chat

- `GET/POST /api/chat/messages/`: Lấy/Gửi tin nhắn
- WebSocket: `ws://localhost:8000/ws/chat/`

## Technologies

- **Backend**: Django, Django REST Framework, Channels (WebSockets)
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)
- **File Processing**: Pydub
- **Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Real-time Communication**: WebSockets

## Contributing

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## License

[MIT License](LICENSE)

## Chức năng quên mật khẩu

Hệ thống cung cấp API cho phép người dùng đặt lại mật khẩu khi quên:

### 1. Yêu cầu đặt lại mật khẩu

```
POST /api/v1/accounts/auth/forgot-password/
```

**Request body:**

```json
{
  "email": "user@example.com"
}
```

**Response:**

```json
{
  "message": "Mã xác nhận đã được gửi đến email của bạn."
}
```

Hệ thống sẽ gửi một token gồm 6 chữ số đến email người dùng.

### 2. Xác thực token và đặt lại mật khẩu

```
POST /api/v1/accounts/auth/verify-reset-token/
```

**Request body:**

```json
{
  "email": "user@example.com",
  "token": "123456",
  "new_password": "NewPassword123"
}
```

**Response:**

```json
{
  "message": "Đặt lại mật khẩu thành công. Vui lòng đăng nhập với mật khẩu mới."
}
```

**Lưu ý:**

- Token chỉ có hiệu lực trong vòng 15 phút
- Mật khẩu mới phải có ít nhất 8 ký tự
- Token chỉ có thể sử dụng một lần

# Spotify Chat Backend - Hướng dẫn Playlist API

## Tổng quan về chức năng Playlist

Hệ thống playlist cho phép người dùng:

- Tạo và quản lý danh sách phát cá nhân
- Đặt chế độ công khai hoặc riêng tư cho playlist
- Thêm/xóa bài hát vào playlist
- Cập nhật ảnh bìa cho playlist
- Theo dõi playlist của người khác

## Đảm bảo quyền riêng tư

Playlist được thiết kế để đảm bảo quyền riêng tư của người dùng:

- Chỉ chủ sở hữu mới có thể chỉnh sửa playlist (thêm/xóa bài hát, cập nhật thông tin)
- Playlist riêng tư (`is_public=False`) chỉ hiển thị cho chủ sở hữu
- Người dùng khác chỉ có thể xem/theo dõi playlist công khai

## API Endpoints cho Playlist

### Danh sách và truy xuất

- `GET /api/v1/music/playlists/` - Lấy danh sách playlist công khai
- `GET /api/v1/music/playlists/{id}/` - Xem chi tiết một playlist
- `GET /api/v1/music/playlists/me/` - Lấy danh sách playlist của người dùng hiện tại

### Tạo và quản lý

- `POST /api/v1/music/playlists/` - Tạo playlist mới
- `PUT/PATCH /api/v1/music/playlists/{id}/` - Cập nhật thông tin playlist
- `DELETE /api/v1/music/playlists/{id}/` - Xóa playlist

### Quản lý bài hát trong playlist

- `POST /api/v1/music/playlists/{id}/add_song/` - Thêm bài hát vào playlist
- `POST /api/v1/music/playlists/{id}/remove_song/` - Xóa bài hát khỏi playlist

### Quản lý ảnh bìa và quyền riêng tư

- `POST /api/v1/music/playlists/{id}/update_cover_image/` - Cập nhật ảnh bìa playlist
- `POST /api/v1/music/playlists/{id}/toggle_privacy/` - Chuyển đổi chế độ công khai/riêng tư

### Theo dõi playlist

- `POST /api/v1/music/playlists/{id}/follow/` - Theo dõi playlist
- `POST /api/v1/music/playlists/{id}/unfollow/` - Bỏ theo dõi playlist
- `GET /api/v1/music/playlists/{id}/followers/` - Xem danh sách người theo dõi playlist

## Ví dụ sử dụng API

### Tạo playlist mới:

```json
POST /api/v1/music/playlists/
{
  "name": "Nhạc Chill Cuối Tuần",
  "description": "Những bài hát nhẹ nhàng, thư giãn cho cuối tuần",
  "is_public": true
}
```

### Thêm bài hát vào playlist:

```json
POST /api/v1/music/playlists/1/add_song/
{
  "song_id": 5
}
```

### Cập nhật ảnh bìa playlist:

```
POST /api/v1/music/playlists/1/update_cover_image/
Content-Type: multipart/form-data
cover_image: [FILE UPLOAD]
```

Hoặc sử dụng ảnh từ bài hát:

```json
POST /api/v1/music/playlists/1/update_cover_image/
{
  "song_id": 5
}
```

### Chuyển đổi chế độ riêng tư:

```json
POST /api/v1/music/playlists/1/toggle_privacy/
```

## Giới hạn và lưu ý

- Mỗi người dùng giới hạn tối đa 50 playlist
- Mỗi playlist giới hạn tối đa 1000 bài hát
- Ảnh bìa playlist: tối đa 5MB, chỉ chấp nhận file JPEG, JPG và PNG
- Không thể thêm trùng bài hát vào playlist
- Chỉ thêm được bài hát có file audio hợp lệ
