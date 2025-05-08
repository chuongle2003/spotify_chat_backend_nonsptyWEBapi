# Music API Documentation

## Cập nhật bài hát (PATCH /api/v1/music/admin/songs/{id}/)

API này cho phép admin cập nhật thông tin bài hát, bao gồm file audio và ảnh bìa.

### Endpoint

```
PATCH /api/v1/music/admin/songs/{id}/
```

### Authentication

- Yêu cầu quyền Admin
- Sử dụng token JWT: `Authorization: Bearer <token>`

### Body

Form-data (multipart/form-data):

| Field        | Type    | Required | Description                    |
| ------------ | ------- | -------- | ------------------------------ |
| title        | string  | No       | Tiêu đề bài hát                |
| artist       | string  | No       | Tên nghệ sĩ                    |
| genre        | string  | No       | Thể loại nhạc                  |
| album        | string  | No       | Tên album                      |
| lyrics       | text    | No       | Lời bài hát                    |
| duration     | integer | No       | Thời lượng (giây)              |
| is_approved  | boolean | No       | Trạng thái phê duyệt           |
| release_date | date    | No       | Ngày phát hành (YYYY-MM-DD)    |
| audio_file   | file    | No       | File âm thanh (mp3, wav, etc.) |
| cover_image  | file    | No       | Ảnh bìa (jpg, png)             |

### Example Request

```bash
# Sử dụng cURL
curl -X PATCH \
  'http://localhost:8000/api/v1/music/admin/songs/1/' \
  -H 'Authorization: Bearer <your_token>' \
  -F 'title=Updated Song Title' \
  -F 'artist=New Artist' \
  -F 'cover_image=@/path/to/new_cover.jpg'
```

### Example Response

```json
{
  "id": 1,
  "title": "Updated Song Title",
  "artist": "New Artist",
  "album": "Album Name",
  "album_info": {
    "id": 2,
    "title": "Album Name",
    "artist": "New Artist"
  },
  "genre": "Pop",
  "genre_info": {
    "id": 1,
    "name": "Pop"
  },
  "duration": 240,
  "audio_file": "http://localhost:8000/media/songs/2023/05/12/song.mp3",
  "cover_image": "http://localhost:8000/media/covers/2023/05/12/new_cover.jpg",
  "lyrics": "Song lyrics...",
  "release_date": "2023-05-12",
  "likes_count": 42,
  "play_count": 1024,
  "comments_count": 5,
  "is_approved": true,
  "uploaded_by": {
    "id": 1,
    "username": "admin",
    "avatar": null
  },
  "created_at": "2023-04-15T10:30:00Z",
  "download_url": "http://localhost:8000/api/v1/music/songs/1/download/",
  "stream_url": "http://localhost:8000/api/v1/music/songs/1/stream/"
}
```

### Lưu ý

1. Các trường không được gửi trong request sẽ giữ nguyên giá trị hiện tại
2. File audio và ảnh bìa chỉ được cập nhật khi gửi kèm trong request
3. Nếu không gửi file mới, hệ thống sẽ giữ nguyên file hiện tại
4. API này yêu cầu multipart/form-data để xử lý upload file
5. Để chỉ cập nhật metadata không kèm file, có thể sử dụng content-type application/json
6. Admin có thể dùng endpoint này để phê duyệt/từ chối bài hát bằng cách thay đổi trường is_approved

### Error Responses

- 400 Bad Request: Dữ liệu không hợp lệ
- 401 Unauthorized: Không có token hoặc token không hợp lệ
- 403 Forbidden: Người dùng không có quyền admin
- 404 Not Found: Không tìm thấy bài hát với ID đã cung cấp
