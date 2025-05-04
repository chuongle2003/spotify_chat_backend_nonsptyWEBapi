# Hướng dẫn sử dụng API Admin cho Spotify Chat

## Giới thiệu

Tài liệu này mô tả chi tiết các API endpoints và quy trình hoạt động dành cho người dùng có quyền admin trong hệ thống Spotify Chat. Các API này cho phép quản lý người dùng, nội dung, tin nhắn, và các chức năng khác trong hệ thống.

## Xác thực

Tất cả các API endpoints của admin đều yêu cầu xác thực JWT và quyền admin.

### Lấy token JWT

```
POST /api/token/
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin_password"
}
```

**Phản hồi thành công:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

Sử dụng token `access` trong header của mọi API request:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...
```

## Quản lý người dùng

### 1. Danh sách người dùng

```
GET /api/admin/users/
```

**Phản hồi:**

```json
[
  {
    "id": 1,
    "username": "user1",
    "email": "user1@example.com",
    "first_name": "Nguyễn",
    "last_name": "Văn A",
    "avatar": "https://example.com/avatars/user1.jpg",
    "bio": "Tôi yêu âm nhạc",
    "created_at": "2023-05-12T10:00:00Z",
    "is_active": true,
    "is_admin": false
  },
  ...
]
```

### 2. Xem chi tiết người dùng

```
GET /api/admin/users/{id}/
```

**Phản hồi:**

```json
{
  "id": 1,
  "username": "user1",
  "email": "user1@example.com",
  "first_name": "Nguyễn",
  "last_name": "Văn A",
  "avatar": "https://example.com/avatars/user1.jpg",
  "bio": "Tôi yêu âm nhạc",
  "created_at": "2023-05-12T10:00:00Z",
  "is_active": true,
  "is_admin": false
}
```

### 3. Xem thông tin đầy đủ của người dùng

```
GET /api/admin/users/{id}/complete/
```

**Phản hồi:**

```json
{
  "id": 1,
  "username": "user1",
  "email": "user1@example.com",
  "first_name": "Nguyễn",
  "last_name": "Văn A",
  "avatar": "https://example.com/avatars/user1.jpg",
  "bio": "Tôi yêu âm nhạc",
  "created_at": "2023-05-12T10:00:00Z",
  "is_active": true,
  "is_admin": false,
  "following_count": 45,
  "followers_count": 30,
  "favorite_songs_count": 120,
  "playlists_count": 8,
  "uploads_count": 12,
  "last_login": "2023-06-01T14:25:00Z"
}
```

### 4. Tạo người dùng mới (Admin)

```
POST /api/admin/users/
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password",
  "first_name": "Trần",
  "last_name": "Thị B",
  "is_active": true,
  "is_admin": false
}
```

### 5. Cập nhật thông tin người dùng

```
PUT /api/admin/users/{id}/
Content-Type: application/json

{
  "username": "updated_username",
  "email": "updated_email@example.com",
  "first_name": "Trần",
  "last_name": "Văn C",
  "bio": "Bio mới",
  "is_active": true
}
```

### 6. Kích hoạt/Vô hiệu hóa tài khoản

```
POST /api/admin/users/{id}/toggle_active/
```

**Phản hồi:**

```json
{
  "status": "User activated"
}
```

hoặc

```json
{
  "status": "User deactivated"
}
```

### 7. Cấp/Thu hồi quyền Admin

```
POST /api/admin/users/{id}/toggle_admin/
```

**Phản hồi:**

```json
{
  "status": "User granted admin access"
}
```

hoặc

```json
{
  "status": "User removed admin access"
}
```

## Quản lý tin nhắn và nội dung

### 1. Xem tất cả tin nhắn

```
GET /api/chat/admin/messages/
```

Tham số tùy chọn:

- `?content_status=NORMAL|FLAGGED|REPORTED|REVIEWED|HIDDEN` - Lọc theo trạng thái
- `?message_type=TEXT|SONG|PLAYLIST|IMAGE|VOICE|FILE` - Lọc theo loại tin nhắn

**Phản hồi:**

```json
[
  {
    "id": 1,
    "sender": 2,
    "receiver": 3,
    "content": "Nội dung tin nhắn",
    "timestamp": "2023-06-01T10:00:00Z",
    "is_read": true,
    "message_type": "TEXT",
    "attachment": null,
    "image": null,
    "voice_note": null,
    "shared_song": null,
    "shared_playlist": null,
    "content_status": "NORMAL",
    "review_note": "",
    "reviewed_by": null,
    "reviewed_at": null,
    "sender_info": {
      "id": 2,
      "username": "user2",
      "avatar": "https://example.com/avatars/user2.jpg"
    },
    "receiver_info": {
      "id": 3,
      "username": "user3",
      "avatar": "https://example.com/avatars/user3.jpg"
    }
  },
  ...
]
```

### 2. Xem chi tiết tin nhắn

```
GET /api/chat/admin/messages/{id}/
```

### 3. Xem báo cáo tin nhắn

```
GET /api/chat/admin/reports/
```

Tham số tùy chọn:

- `?status=PENDING|REVIEWED|RESOLVED|DISMISSED` - Lọc theo trạng thái
- `?reason=INAPPROPRIATE|SPAM|HARASSMENT|HATE_SPEECH|OTHER` - Lọc theo lý do

**Phản hồi:**

```json
[
  {
    "id": 1,
    "message": {
      "id": 123,
      "content": "Nội dung tin nhắn bị báo cáo",
      "sender_info": {
        "id": 5,
        "username": "reported_user"
      }
    },
    "reporter": {
      "id": 8,
      "username": "reporter_user"
    },
    "reason": "INAPPROPRIATE",
    "description": "Tin nhắn này vi phạm quy định",
    "timestamp": "2023-06-02T11:30:00Z",
    "status": "PENDING",
    "handled_by": null,
    "handled_at": null,
    "action_taken": ""
  },
  ...
]
```

### 4. Xem chi tiết báo cáo tin nhắn

```
GET /api/chat/admin/reports/{id}/
```

### 5. Cập nhật trạng thái báo cáo

```
PUT /api/chat/admin/reports/{id}/
Content-Type: application/json

{
  "status": "RESOLVED",
  "action_taken": "Đã xử lý và ẩn tin nhắn vi phạm"
}
```

### 6. Thống kê báo cáo tin nhắn

```
GET /api/chat/admin/reports/statistics/
```

**Phản hồi:**

```json
{
  "total_reports": 56,
  "pending_reports": 12,
  "resolved_reports": 37,
  "dismissed_reports": 7,
  "by_reason": {
    "INAPPROPRIATE": 23,
    "SPAM": 15,
    "HARASSMENT": 11,
    "HATE_SPEECH": 5,
    "OTHER": 2
  },
  "recent_trend": [
    { "date": "2023-06-01", "count": 5 },
    { "date": "2023-06-02", "count": 8 },
    { "date": "2023-06-03", "count": 3 }
  ]
}
```

### 7. Xem báo cáo đang chờ xử lý

```
GET /api/chat/admin/reports/pending/
```

## Quản lý Hạn chế Chat

### 1. Xem tất cả hạn chế

```
GET /api/chat/admin/restrictions/
```

**Phản hồi:**

```json
[
  {
    "id": 1,
    "user": {
      "id": 5,
      "username": "restricted_user"
    },
    "restriction_type": "TEMPORARY",
    "reason": "Vi phạm quy định chat nhiều lần",
    "created_at": "2023-06-01T09:00:00Z",
    "expires_at": "2023-06-08T09:00:00Z",
    "created_by": {
      "id": 1,
      "username": "admin"
    },
    "is_active": true,
    "is_expired": false
  },
  ...
]
```

### 2. Tạo hạn chế mới

```
POST /api/chat/admin/restrictions/
Content-Type: application/json

{
  "user": 5,
  "restriction_type": "TEMPORARY",
  "reason": "Vi phạm quy định chat nhiều lần",
  "expires_at": "2023-06-08T09:00:00Z",
  "is_active": true
}
```

### 3. Cập nhật hạn chế

```
PUT /api/chat/admin/restrictions/{id}/
Content-Type: application/json

{
  "is_active": false
}
```

### 4. Xem thống kê chat của người dùng

```
GET /api/chat/admin/stats/{user_id}/
```

**Phản hồi:**

```json
{
  "user": {
    "id": 5,
    "username": "user5"
  },
  "total_messages": 253,
  "messages_by_type": {
    "TEXT": 180,
    "IMAGE": 42,
    "SONG": 26,
    "PLAYLIST": 5
  },
  "active_conversations": 15,
  "reports_received": 3,
  "reports_created": 7,
  "last_message_date": "2023-06-04T15:30:22Z",
  "daily_activity": [
    { "date": "2023-06-01", "count": 25 },
    { "date": "2023-06-02", "count": 18 },
    { "date": "2023-06-03", "count": 30 }
  ]
}
```

## Quản lý playlist cộng tác

### 1. Xem tất cả playlist cộng tác

```
GET /api/music/admin/playlists/collaborative/
```

**Phản hồi:**

```json
[
  {
    "id": 10,
    "name": "Summer Party Mix",
    "description": "Playlist cộng tác cho mùa hè",
    "owner": {
      "id": 3,
      "username": "playlist_creator"
    },
    "cover_image": "https://example.com/playlists/10.jpg",
    "created_at": "2023-05-15T10:00:00Z",
    "is_collaborative": true,
    "collaborator_count": 5
  },
  ...
]
```

### 2. Xem chi tiết playlist cộng tác

```
GET /api/music/admin/playlists/collaborative/{id}/
```

### 3. Xem danh sách người cộng tác trên playlist

```
GET /api/music/admin/playlists/{playlist_id}/collaborators/
```

**Phản hồi:**

```json
[
  {
    "id": 3,
    "user": {
      "id": 5,
      "username": "collaborator1"
    },
    "playlist": 10,
    "role": "EDITOR",
    "added_at": "2023-05-16T11:00:00Z",
    "added_by": {
      "id": 3,
      "username": "playlist_creator"
    }
  },
  ...
]
```

### 4. Thêm người cộng tác vào playlist

```
POST /api/music/admin/playlists/{playlist_id}/collaborators/add/
Content-Type: application/json

{
  "user_id": 7,
  "role": "VIEWER"
}
```

### 5. Thay đổi quyền người cộng tác

```
PUT /api/music/admin/playlists/{playlist_id}/collaborators/{user_id}/role/
Content-Type: application/json

{
  "role": "EDITOR"
}
```

### 6. Xem lịch sử chỉnh sửa playlist

```
GET /api/music/admin/playlists/{playlist_id}/edit_history/
```

**Phản hồi:**

```json
[
  {
    "id": 25,
    "playlist": 10,
    "user": {
      "id": 5,
      "username": "collaborator1"
    },
    "action": "ADD_SONG",
    "timestamp": "2023-05-18T14:30:00Z",
    "details": {
      "song_id": 324,
      "song_title": "Example Song"
    }
  },
  ...
]
```

### 7. Khôi phục playlist về trạng thái trước đó

```
POST /api/music/admin/playlists/{playlist_id}/restore/
Content-Type: application/json

{
  "history_id": 15
}
```

## Quản lý Âm nhạc

### 1. Quản lý Bài hát

#### 1.1. Xem danh sách bài hát

```
GET /api/music/songs/
```

**Tham số tùy chọn:**

- `?title=từ khóa` - Lọc theo tên bài hát
- `?artist=từ khóa` - Lọc theo nghệ sĩ
- `?genre=tên thể loại` - Lọc theo thể loại

**Phản hồi:**

```json
[
  {
    "id": 123,
    "title": "Bài hát 1",
    "artist": "Nghệ sĩ A",
    "album": "Album X",
    "duration": 240,
    "audio_file": "https://example.com/songs/123.mp3",
    "cover_image": "https://example.com/covers/123.jpg",
    "genre": "Nhạc Trẻ",
    "likes_count": 42,
    "play_count": 1024,
    "uploaded_by": {
      "id": 5,
      "username": "user5"
    },
    "created_at": "2023-05-15T10:00:00Z",
    "release_date": "2023-04-01"
  },
  ...
]
```

#### 1.2. Xem chi tiết bài hát

```
GET /api/music/songs/{id}/
```

#### 1.3. Cập nhật thông tin bài hát

```
PUT /api/music/songs/{id}/
Content-Type: application/json

{
  "title": "Tên bài hát cập nhật",
  "artist": "Tên nghệ sĩ cập nhật",
  "album": "Tên album cập nhật",
  "genre": "Thể loại cập nhật",
  "release_date": "2023-05-01"
}
```

#### 1.4. Xóa bài hát

```
DELETE /api/music/songs/{id}/
```

#### 1.5. Thêm bài hát mới

```
POST /api/music/songs/
Content-Type: multipart/form-data

{
  "title": "Tên bài hát mới",
  "artist": "Tên nghệ sĩ",
  "album": "Tên album",
  "genre": "Thể loại",
  "audio_file": (file âm thanh),
  "cover_image": (hình ảnh bìa),
  "release_date": "2023-06-01"
}
```

### 2. Quản lý Nghệ sĩ

#### 2.1. Xem danh sách nghệ sĩ

```
GET /api/music/artists/
```

**Phản hồi:**

```json
[
  {
    "id": 45,
    "name": "Tên nghệ sĩ",
    "bio": "Tiểu sử nghệ sĩ",
    "image": "https://example.com/artists/45.jpg"
  },
  ...
]
```

#### 2.2. Xem chi tiết nghệ sĩ

```
GET /api/music/artists/{id}/
```

#### 2.3. Cập nhật thông tin nghệ sĩ

```
PUT /api/music/artists/{id}/
Content-Type: application/json

{
  "name": "Tên nghệ sĩ cập nhật",
  "bio": "Tiểu sử cập nhật"
}
```

#### 2.4. Thêm nghệ sĩ mới

```
POST /api/music/artists/
Content-Type: multipart/form-data

{
  "name": "Tên nghệ sĩ mới",
  "bio": "Tiểu sử nghệ sĩ",
  "image": (hình ảnh nghệ sĩ)
}
```

### 3. Quản lý Thể loại (Genre)

#### 3.1. Xem danh sách thể loại

```
GET /api/music/genres/
```

**Phản hồi:**

```json
[
  {
    "id": 12,
    "name": "Nhạc Trẻ",
    "description": "Nhạc hiện đại dành cho giới trẻ",
    "image": "https://example.com/genres/12.jpg",
    "songs_count": 245
  },
  ...
]
```

#### 3.2. Thêm thể loại mới

```
POST /api/music/genres/
Content-Type: multipart/form-data

{
  "name": "Tên thể loại mới",
  "description": "Mô tả thể loại",
  "image": (hình ảnh thể loại)
}
```

#### 3.3. Cập nhật thể loại

```
PUT /api/music/genres/{id}/
Content-Type: application/json

{
  "name": "Tên thể loại cập nhật",
  "description": "Mô tả cập nhật"
}
```

### 4. Quản lý Album

#### 4.1. Xem danh sách album

```
GET /api/music/albums/
```

**Phản hồi:**

```json
[
  {
    "id": 34,
    "title": "Tên album",
    "artist": "Tên nghệ sĩ",
    "cover_image": "https://example.com/albums/34.jpg",
    "release_date": "2023-03-15",
    "description": "Mô tả album"
  },
  ...
]
```

#### 4.2. Xem chi tiết album

```
GET /api/music/albums/{id}/
```

**Phản hồi:**

```json
{
  "id": 34,
  "title": "Tên album",
  "artist": "Tên nghệ sĩ",
  "cover_image": "https://example.com/albums/34.jpg",
  "release_date": "2023-03-15",
  "description": "Mô tả album",
  "songs": [
    {
      "id": 123,
      "title": "Bài hát 1",
      "duration": 240,
      "audio_file": "https://example.com/songs/123.mp3"
    },
    ...
  ]
}
```

#### 4.3. Thêm album mới

```
POST /api/music/albums/
Content-Type: multipart/form-data

{
  "title": "Tên album mới",
  "artist": "Tên nghệ sĩ",
  "release_date": "2023-06-01",
  "cover_image": (hình ảnh bìa album),
  "description": "Mô tả album"
}
```

#### 4.4. Cập nhật album

```
PUT /api/music/albums/{id}/
Content-Type: application/json

{
  "title": "Tên album cập nhật",
  "description": "Mô tả cập nhật"
}
```

### 5. Thống kê và Báo cáo

#### 5.1. Thống kê tổng quan

```
GET /api/music/admin/statistics/
```

**Phản hồi:**

```json
{
  "overview": {
    "total_songs": 1245,
    "total_playlists": 560,
    "total_users": 850,
    "active_users": 345,
    "total_plays": 105678
  },
  "genre_stats": {
    "Nhạc Trẻ": {
      "song_count": 450,
      "total_plays": 45000,
      "avg_plays": 100
    },
    "Ballad": {
      "song_count": 300,
      "total_plays": 30000,
      "avg_plays": 100
    }
  },
  "monthly_plays": {
    "2023-06-01": 1500,
    "2023-06-02": 1600,
    "2023-06-03": 1450
  },
  "top_songs": [
    {
      "id": 123,
      "title": "Bài hát hot 1",
      "artist": "Nghệ sĩ A",
      "play_count": 5000
    }
  ],
  "top_playlists": [
    {
      "id": 45,
      "name": "Playlist nổi bật",
      "user": "username1",
      "followers_count": 250
    }
  ]
}
```

#### 5.2. Báo cáo top bài hát

```
GET /api/music/admin/reports/top-songs/
```

**Tham số tùy chọn:**

- `?period=day|week|month|year` - Khoảng thời gian (mặc định: month)
- `?limit=10` - Số lượng kết quả (mặc định: 10)

#### 5.3. Báo cáo top thể loại

```
GET /api/music/admin/reports/top-genres/
```

#### 5.4. Báo cáo tăng trưởng người dùng

```
GET /api/music/admin/reports/user-growth/
```

#### 5.5. Báo cáo mức độ tương tác

```
GET /api/music/admin/reports/engagement/
```

### 6. Kiểm duyệt nội dung

#### 6.1. Xem bài hát cần kiểm duyệt

```
GET /api/music/admin/moderation/songs/
```

**Tham số:**

- `?status=pending|approved|rejected` - Lọc theo trạng thái

**Phản hồi:**

```json
[
  {
    "id": 123,
    "title": "Bài hát cần kiểm duyệt",
    "artist": "Nghệ sĩ A",
    "uploaded_by": {
      "id": 5,
      "username": "user5"
    },
    "status": "pending",
    "created_at": "2023-06-01T10:00:00Z",
    "notes": ""
  },
  ...
]
```

#### 6.2. Phê duyệt/Từ chối bài hát

```
PUT /api/music/admin/moderation/songs/{id}/
Content-Type: application/json

{
  "status": "approved", // hoặc "rejected"
  "notes": "Lý do chấp nhận/từ chối"
}
```

## Quy trình Quản lý Âm nhạc

1. **Kiểm soát nội dung mới**:

   - Admin xem các bài hát mới được tải lên thông qua API `/api/music/admin/moderation/songs/`
   - Đánh giá chất lượng âm thanh và nội dung
   - Phê duyệt hoặc từ chối bài hát

2. **Quản lý thể loại**:

   - Thêm thể loại mới khi cần thiết thông qua API `/api/music/genres/`
   - Cập nhật mô tả và hình ảnh thể loại để thu hút người dùng
   - Theo dõi thể loại phổ biến thông qua báo cáo thống kê

3. **Quản lý nghệ sĩ**:

   - Thêm thông tin nghệ sĩ mới thông qua API `/api/music/artists/`
   - Cập nhật tiểu sử và hình ảnh nghệ sĩ để đảm bảo thông tin chính xác
   - Kết nối bài hát với nghệ sĩ đúng

4. **Quản lý album**:

   - Tạo album cho các bộ sưu tập bài hát
   - Cập nhật thông tin và hình ảnh album
   - Đảm bảo tất cả bài hát trong album được phân loại chính xác

5. **Theo dõi xu hướng**:
   - Kiểm tra báo cáo thường xuyên thông qua API thống kê
   - Cập nhật danh sách "Đề xuất" và "Xu hướng" dựa trên dữ liệu phân tích
   - Điều chỉnh việc hiển thị nội dung trên trang chính dựa trên dữ liệu người dùng

## Quy trình Quản lý Người dùng

1. **Kiểm tra tài khoản**:

   - Admin xem danh sách người dùng thông qua API `GET /api/admin/users/`
   - Kiểm tra thông tin chi tiết của người dùng thông qua API `GET /api/admin/users/{id}/complete/`

2. **Xử lý quyền admin**:

   - Cấp quyền admin cho người dùng đáng tin cậy thông qua API `POST /api/admin/users/{id}/toggle_admin/`
   - Khi người dùng được cấp quyền admin, họ có thể truy cập tất cả các API admin

3. **Vô hiệu hóa tài khoản vi phạm**:
   - Nếu phát hiện tài khoản vi phạm nghiêm trọng, admin có thể vô hiệu hóa tài khoản thông qua API `POST /api/admin/users/{id}/toggle_active/`
   - Tài khoản bị vô hiệu hóa không thể đăng nhập vào hệ thống

## Lưu ý về bảo mật

1. **Giữ an toàn token**:

   - Không chia sẻ token JWT với người khác
   - Lưu trữ token an toàn trên client
   - Refresh token khi hết hạn

2. **Quyền admin**:

   - Chỉ cấp quyền admin cho người dùng đáng tin cậy
   - Kiểm tra log hoạt động thường xuyên
   - Hủy bỏ quyền admin khi không còn cần thiết

3. **Xử lý dữ liệu nhạy cảm**:
   - Tuân thủ quy định về bảo vệ dữ liệu cá nhân
   - Không chia sẻ thông tin người dùng ra bên ngoài
   - Chỉ lưu trữ thông tin cần thiết trong quá trình xử lý báo cáo

## Hiện trạng API

Tất cả các API đề cập trong tài liệu này đều đã được triển khai và sẵn sàng sử dụng. Nếu có thay đổi hoặc bổ sung API mới, tài liệu sẽ được cập nhật tương ứng.
