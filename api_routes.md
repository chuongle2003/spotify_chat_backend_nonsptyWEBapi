# API Routes - Spotify Chat Backend

## Documentation Endpoints

- `GET /api/schema/` - OpenAPI schema
- `GET /api/schema/swagger-ui/` - Swagger UI
- `GET /api/redoc/` - ReDoc UI

## Authentication Endpoints

- `POST /api/token/` - Đăng nhập và nhận JWT token
- `POST /api/token/refresh/` - Làm mới JWT token

## Account Endpoints

Base: `/api/accounts/`

### User Management

- `GET /api/accounts/users/` - Danh sách người dùng
- `POST /api/accounts/users/` - Đăng ký tài khoản mới
- `GET /api/accounts/users/{id}/` - Chi tiết người dùng
- `PUT/PATCH /api/accounts/users/{id}/` - Cập nhật thông tin người dùng
- `DELETE /api/accounts/users/{id}/` - Xóa người dùng

### User Profile & Social

- `GET /api/accounts/users/me/` - Thông tin người dùng hiện tại
- `POST /api/accounts/users/{id}/follow/` - Theo dõi người dùng
- `POST /api/accounts/users/{id}/unfollow/` - Bỏ theo dõi người dùng

## Music Endpoints

Base: `/api/music/`

### Xem thông tin

- `GET /api/music/songs/` - Danh sách bài hát
- `GET /api/music/songs/{id}/` - Chi tiết bài hát
- `GET /api/music/playlists/` - Danh sách playlist
- `GET /api/music/playlists/{id}/` - Chi tiết playlist
- `GET /api/music/albums/` - Danh sách album
- `GET /api/music/albums/{id}/` - Chi tiết album
- `GET /api/music/genres/` - Danh sách thể loại
- `GET /api/music/genres/{id}/` - Chi tiết thể loại

### Tương tác với bài hát

- `POST /api/music/songs/` - Thêm bài hát mới
- `POST /api/music/songs/{id}/play/` - Nghe bài hát
- `POST /api/music/songs/{id}/like/` - Thích/bỏ thích bài hát
- `POST /api/music/upload/` - Upload file nhạc

### Playlist

- `POST /api/music/playlists/` - Tạo playlist
- `POST /api/music/playlists/{id}/add_song/` - Thêm bài hát vào playlist
- `POST /api/music/playlists/{id}/remove_song/` - Xóa bài hát khỏi playlist
- `POST /api/music/playlists/{id}/follow/` - Theo dõi playlist
- `POST /api/music/playlists/{id}/unfollow/` - Bỏ theo dõi playlist
- `GET /api/music/playlists/` - Danh sách playlist của user
- `POST /api/music/playlists/create/` - Tạo playlist mới

### Tìm kiếm & Khám phá

- `GET /api/music/songs/search/?q=query` - Tìm kiếm bài hát
- `GET /api/music/songs/trending/` - Bài hát đang thịnh hành
- `GET /api/music/songs/recommended/` - Đề xuất bài hát
- `GET /api/music/public/search/?q=query` - Tìm kiếm công khai
- `GET /api/music/public/playlists/` - Playlist công khai

### Đánh giá & Bình luận

- `GET /api/music/comments/` - Danh sách bình luận
- `POST /api/music/comments/` - Thêm bình luận
- `GET /api/music/ratings/` - Danh sách đánh giá
- `POST /api/music/ratings/` - Thêm đánh giá

### Thư viện cá nhân

- `GET /api/music/library/` - Thư viện nhạc cá nhân

## Chat Endpoints

Base: `/api/chat/`

### Tin nhắn

- `GET /api/chat/messages/` - Danh sách tin nhắn của người dùng
- `POST /api/chat/messages/` - Gửi tin nhắn mới
- `GET /api/chat/messages/{id}/` - Chi tiết tin nhắn
- `PUT/PATCH /api/chat/messages/{id}/` - Cập nhật tin nhắn
- `DELETE /api/chat/messages/{id}/` - Xóa tin nhắn

### Cuộc trò chuyện

- `GET /api/chat/conversations/` - Danh sách cuộc trò chuyện
- `GET /api/chat/conversations/{user_id}/` - Xem tin nhắn với một người dùng cụ thể

### WebSocket

- `ws://domain/ws/chat/{room_name}/` - Kết nối WebSocket cho chat real-time

## Feature Maps

### Người dùng chưa đăng nhập

- `GET /api/music/public/features/` - Danh sách tính năng công khai
  - Xem playlist công khai
  - Tìm kiếm công khai
  - Xem bài hát thịnh hành

### Người dùng đã đăng nhập

- `GET /api/music/features/basic/` - Danh sách tính năng cho người dùng đã đăng nhập
  - Quản lý playlist cá nhân
  - Tạo playlist
  - Quản lý hồ sơ
  - Tải lên bài hát
  - Xem thư viện
  - Tìm kiếm
