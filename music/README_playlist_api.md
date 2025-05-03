# API Playlist - Tài liệu cho Client

## Các Endpoint của Playlist

### 1. Lấy danh sách playlist

**Endpoint**: `GET /api/v1/music/playlists/`

**Mô tả**: Lấy danh sách tất cả playlist công khai và playlist của người dùng hiện tại

**Yêu cầu**: Không cần xác thực để xem playlist công khai, cần xác thực để xem cả playlist cá nhân

**Tham số URL**:

- `?page=1` - Trang hiện tại (mặc định: 1)
- `?page_size=20` - Số lượng playlist mỗi trang (mặc định: 20)

**Phản hồi thành công**:

```json
[
  {
    "id": 1,
    "name": "Nhạc Chill Cuối Tuần",
    "description": "Những bài hát nhẹ nhàng, thư giãn cho cuối tuần",
    "cover_image": "http://example.com/media/playlist_covers/1.jpg",
    "is_public": true,
    "songs_count": 15,
    "user": {
      "id": 1,
      "username": "user1"
    }
  },
  ...
]
```

### 2. Xem chi tiết playlist

**Endpoint**: `GET /api/v1/music/playlists/{id}/`

**Mô tả**: Xem thông tin chi tiết và danh sách bài hát trong playlist

**Yêu cầu**: Không cần xác thực để xem playlist công khai, chỉ chủ sở hữu mới có thể xem playlist riêng tư

**Phản hồi thành công**:

```json
{
  "id": 1,
  "name": "Nhạc Chill Cuối Tuần",
  "description": "Những bài hát nhẹ nhàng, thư giãn cho cuối tuần",
  "cover_image": "http://example.com/media/playlist_covers/1.jpg",
  "is_public": true,
  "created_at": "2023-01-15T08:30:00Z",
  "updated_at": "2023-01-16T10:45:00Z",
  "user": {
    "id": 1,
    "username": "user1"
  },
  "songs": [
    {
      "id": 5,
      "title": "Hạ Còn Vương Nắng",
      "artist": "DATKAA",
      "audio_file": "http://example.com/media/songs/5.mp3",
      "cover_image": "http://example.com/media/covers/5.jpg",
      "duration": 240
    },
    ...
  ],
  "followers_count": 10
}
```

**Phản hồi lỗi** (truy cập playlist riêng tư):

```json
{
  "error": "Bạn không có quyền xem playlist riêng tư này"
}
```

### 3. Lấy playlist của người dùng hiện tại

**Endpoint**: `GET /api/v1/music/playlists/`

**Mô tả**: Lấy danh sách tất cả playlist do người dùng hiện tại tạo

**Yêu cầu**: Cần xác thực

**Phản hồi thành công**: Tương tự như endpoint `GET /api/v1/music/playlists/` nhưng chỉ trả về playlist của người dùng hiện tại

### 4. Tạo playlist mới

**Endpoint**: `POST /api/v1/music/playlists/`

**Mô tả**: Tạo một playlist mới

**Yêu cầu**: Cần xác thực

**Body**:

```json
{
  "name": "Nhạc Chill Cuối Tuần",
  "description": "Những bài hát nhẹ nhàng, thư giãn cho cuối tuần",
  "is_public": true
}
```

**Phản hồi thành công**:

```json
{
  "id": 1,
  "name": "Nhạc Chill Cuối Tuần",
  "description": "Những bài hát nhẹ nhàng, thư giãn cho cuối tuần",
  "cover_image": null,
  "is_public": true,
  "created_at": "2023-01-15T08:30:00Z",
  "updated_at": "2023-01-15T08:30:00Z",
  "user": {
    "id": 1,
    "username": "user1"
  },
  "songs": [],
  "followers_count": 0
}
```

**Phản hồi lỗi**:

```json
{
  "error": "Tên playlist không được để trống"
}
```

hoặc

```json
{
  "error": "Bạn đã đạt giới hạn tối đa 50 playlist"
}
```

### 5. Cập nhật thông tin playlist

**Endpoint**: `PUT/PATCH /api/v1/music/playlists/{id}/`

**Mô tả**: Cập nhật thông tin của playlist

**Yêu cầu**: Cần xác thực và phải là chủ sở hữu playlist

**Body**:

```json
{
  "name": "Nhạc Chill Cuối Tuần (Mới)",
  "description": "Playlist nhạc chill đã cập nhật",
  "is_public": false
}
```

**Phản hồi thành công**:

```json
{
  "id": 1,
  "name": "Nhạc Chill Cuối Tuần (Mới)",
  "description": "Playlist nhạc chill đã cập nhật",
  "is_public": false,
  ...
}
```

**Phản hồi lỗi**:

```json
{
  "error": "Bạn không có quyền chỉnh sửa playlist này"
}
```

### 6. Xóa playlist

**Endpoint**: `DELETE /api/v1/music/playlists/{id}/`

**Mô tả**: Xóa một playlist

**Yêu cầu**: Cần xác thực và phải là chủ sở hữu playlist

**Phản hồi thành công**:

```
Status: 204 No Content
```

**Phản hồi lỗi**:

```json
{
  "error": "Bạn không có quyền xóa playlist này"
}
```

### 7. Thêm bài hát vào playlist

**Endpoint**: `POST /api/v1/music/playlists/{id}/add_song/`

**Mô tả**: Thêm một bài hát vào playlist

**Yêu cầu**: Cần xác thực và phải là chủ sở hữu playlist

**Body**:

```json
{
  "song_id": 5
}
```

**Phản hồi thành công**:

```json
{
  "status": "Đã thêm bài hát vào playlist"
}
```

**Phản hồi lỗi**:

```json
{
  "error": "Bạn không có quyền chỉnh sửa playlist này"
}
```

hoặc

```json
{
  "error": "Bài hát đã có trong playlist"
}
```

hoặc

```json
{
  "error": "Không tìm thấy bài hát"
}
```

hoặc

```json
{
  "error": "Playlist đã đạt giới hạn tối đa 1000 bài hát"
}
```

### 8. Xóa bài hát khỏi playlist

**Endpoint**: `POST /api/v1/music/playlists/{id}/remove_song/`

**Mô tả**: Xóa một bài hát khỏi playlist

**Yêu cầu**: Cần xác thực và phải là chủ sở hữu playlist

**Body**:

```json
{
  "song_id": 5
}
```

**Phản hồi thành công**:

```json
{
  "status": "Đã xóa bài hát khỏi playlist"
}
```

**Phản hồi lỗi**:

```json
{
  "error": "Bạn không có quyền chỉnh sửa playlist này"
}
```

hoặc

```json
{
  "error": "Bài hát không có trong playlist"
}
```

### 9. Cập nhật ảnh bìa playlist

**Endpoint**: `POST /api/v1/music/playlists/{id}/update_cover_image/`

**Mô tả**: Cập nhật ảnh bìa cho playlist

**Yêu cầu**: Cần xác thực và phải là chủ sở hữu playlist

**Body** (form-data):

```
cover_image: [FILE UPLOAD]
```

**Hoặc Body** (json):

```json
{
  "song_id": 5 // Lấy ảnh bìa từ bài hát
}
```

**Phản hồi thành công**:

```json
{
  "status": "Đã cập nhật ảnh bìa thành công"
}
```

hoặc

```json
{
  "status": "Đã cập nhật ảnh bìa từ bài hát"
}
```

**Phản hồi lỗi**:

```json
{
  "error": "Kích thước ảnh không được vượt quá 5MB"
}
```

hoặc

```json
{
  "error": "Định dạng ảnh không hợp lệ. Chỉ chấp nhận JPEG, JPG và PNG"
}
```

### 10. Chuyển đổi chế độ công khai/riêng tư

**Endpoint**: `POST /api/v1/music/playlists/{id}/toggle_privacy/`

**Mô tả**: Chuyển đổi trạng thái công khai/riêng tư của playlist

**Yêu cầu**: Cần xác thực và phải là chủ sở hữu playlist

**Phản hồi thành công**:

```json
{
  "status": "Đã chuyển playlist sang chế độ công khai"
}
```

hoặc

```json
{
  "status": "Đã chuyển playlist sang chế độ riêng tư"
}
```

### 11. Theo dõi playlist

**Endpoint**: `POST /api/v1/music/playlists/{id}/follow/`

**Mô tả**: Theo dõi một playlist

**Yêu cầu**: Cần xác thực và playlist phải là công khai hoặc của chính người dùng

**Phản hồi thành công**:

```json
{
  "status": "Đã theo dõi playlist thành công"
}
```

**Phản hồi lỗi**:

```json
{
  "error": "Bạn đã theo dõi playlist này rồi"
}
```

hoặc

```json
{
  "error": "Bạn không có quyền xem playlist riêng tư này"
}
```

### 12. Bỏ theo dõi playlist

**Endpoint**: `POST /api/v1/music/playlists/{id}/unfollow/`

**Mô tả**: Bỏ theo dõi một playlist

**Yêu cầu**: Cần xác thực

**Phản hồi thành công**:

```json
{
  "status": "Đã bỏ theo dõi playlist thành công"
}
```

**Phản hồi lỗi**:

```json
{
  "error": "Bạn chưa theo dõi playlist này"
}
```

### 13. Xem danh sách người theo dõi playlist

**Endpoint**: `GET /api/v1/music/playlists/{id}/followers/`

**Mô tả**: Xem danh sách người dùng đang theo dõi playlist

**Yêu cầu**: Cần xác thực và playlist phải là công khai hoặc của chính người dùng

**Phản hồi thành công**:

```json
{
  "playlist_id": 1,
  "playlist_name": "Nhạc Chill Cuối Tuần",
  "followers_count": 10,
  "followers": [
    {
      "id": 2,
      "username": "user2",
      "avatar": "http://example.com/media/avatars/user2.jpg"
    },
    ...
  ]
}
```

**Phản hồi lỗi**:

```json
{
  "error": "Bạn không có quyền xem thông tin playlist riêng tư này"
}
```

### 14. Lấy danh sách playlist nổi bật

**Endpoint**: `GET /api/v1/music/playlists/featured/`

**Mô tả**: Lấy danh sách playlist công khai được nhiều người theo dõi nhất

**Yêu cầu**: Không cần xác thực

**Tham số URL**:

- `?page=1` - Trang hiện tại (mặc định: 1)
- `?page_size=20` - Số lượng playlist mỗi trang (mặc định: 20)

**Phản hồi thành công**:

```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "playlists": [
    {
      "id": 1,
      "name": "Nhạc Chill Cuối Tuần",
      "description": "Những bài hát nhẹ nhàng, thư giãn cho cuối tuần",
      "cover_image": "http://example.com/media/playlist_covers/1.jpg",
      "is_public": true,
      "songs_count": 15,
      "followers_count": 250,
      "user": {
        "id": 1,
        "username": "user1"
      }
    },
    ...
  ]
}
```

### 15. Chia sẻ playlist

**Endpoint**: `POST /api/v1/music/share/playlist/{id}/`

**Mô tả**: Chia sẻ playlist với một người dùng khác qua tin nhắn

**Yêu cầu**: Cần xác thực

**Body**:

```json
{
  "receiver_id": 2,
  "content": "Playlist này hay lắm, nghe thử đi bạn!"
}
```

**Phản hồi thành công**:

```json
{
  "id": 1,
  "sender": {
    "id": 1,
    "username": "user1"
  },
  "receiver": {
    "id": 2,
    "username": "user2"
  },
  "content": "Playlist này hay lắm, nghe thử đi bạn!",
  "message_type": "PLAYLIST",
  "shared_playlist": {
    "id": 1,
    "name": "Nhạc Chill Cuối Tuần"
  },
  "timestamp": "2023-01-15T08:30:00Z",
  "is_read": false
}
```

## Lưu ý về quyền hạn

1. **Xem playlist**:

   - Playlist công khai: Ai cũng có thể xem
   - Playlist riêng tư: Chỉ chủ sở hữu có thể xem

2. **Chỉnh sửa playlist**:

   - Chỉ chủ sở hữu có thể thêm/xóa bài hát, cập nhật thông tin, thay đổi ảnh bìa
   - Không thể chỉnh sửa playlist của người khác

3. **Theo dõi playlist**:
   - Chỉ có thể theo dõi playlist công khai
   - Không thể theo dõi playlist riêng tư của người khác

## Giới hạn

1. **Số lượng**:

   - Mỗi người dùng tối đa 50 playlist
   - Mỗi playlist tối đa 1000 bài hát

2. **Ảnh bìa**:

   - Kích thước tối đa: 5MB
   - Định dạng hỗ trợ: JPEG, JPG, PNG

3. **Bài hát**:
   - Không thể thêm trùng bài hát vào playlist
   - Chỉ thêm được bài hát có file audio hợp lệ
