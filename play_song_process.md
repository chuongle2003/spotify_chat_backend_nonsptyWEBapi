# Quy trình phát nhạc trong hệ thống

## I. Các bước cơ bản để phát một bài hát

### A. Đối với người dùng đã đăng nhập:

1. **Bước 1: Xác thực người dùng**

   - Người dùng đăng nhập vào hệ thống bằng email và mật khẩu
   - Hệ thống xác thực và cấp token cho người dùng
   - Token được lưu trữ để sử dụng cho các yêu cầu API tiếp theo

2. **Bước 2: Tìm kiếm và chọn bài hát**

   - Người dùng có thể tìm bài hát qua các cách sau:
     - Tìm kiếm theo tên, nghệ sĩ, album qua endpoint `/search/`
     - Duyệt qua các bài hát thịnh hành qua `/trending/`
     - Xem các bài hát được đề xuất qua `/recommended/`
     - Xem thư viện cá nhân qua `/library/`
     - Duyệt qua các playlist cá nhân hoặc công khai

3. **Bước 3: Tương tác với bài hát**

   - Người dùng chọn bài hát để phát
   - Client gửi yêu cầu đến endpoint `/api/songs/{id}/play/`
   - Server xử lý yêu cầu thông qua `SongViewSet.play()` method
   - Hệ thống kiểm tra quyền truy cập của người dùng đối với bài hát

4. **Bước 4: Xử lý phát nhạc trên server**

   - Hệ thống tăng `play_count` của bài hát lên 1
   - Hệ thống tạo bản ghi mới trong `SongPlayHistory` để lưu lượt nghe
   - Hệ thống trả về URL streaming hoặc file âm thanh

5. **Bước 5: Phát nhạc trên client**

   - Client nhận dữ liệu âm thanh hoặc URL streaming
   - Trình phát nhạc được khởi động để phát bài hát
   - Người dùng có thể tương tác với bài hát (tạm dừng, tiếp tục, tua)

6. **Bước 6: Ghi nhận hoạt động và cập nhật đề xuất**
   - Lịch sử nghe được sử dụng để cập nhật đề xuất cho người dùng
   - Hệ thống phân tích sở thích thể loại qua lịch sử nghe
   - Đề xuất bài hát được cập nhật dựa trên dữ liệu mới nhất

### B. Đối với người dùng chưa đăng nhập (khách):

1. **Bước 1: Tìm kiếm và chọn bài hát**

   - Người dùng có thể tìm bài hát qua các cách sau:
     - Tìm kiếm cơ bản qua `/public/search/`
     - Duyệt qua các bài hát thịnh hành qua `/trending/`
     - Xem các playlist công khai qua `/public/playlists/`

2. **Bước 2: Tương tác với bài hát**

   - Người dùng chọn bài hát để phát
   - Client gửi yêu cầu đến endpoint `/api/songs/{id}/play/`
   - Server xử lý yêu cầu và kiểm tra bài hát có phải công khai không

3. **Bước 3: Phát nhạc**
   - Hệ thống trả về URL streaming hoặc file âm thanh
   - Client phát bài hát
   - Không ghi nhận lịch sử nghe và không tăng play_count

## II. Luồng dữ liệu chi tiết khi phát nhạc

1. **Client gửi request đến API**:

   ```http
   POST /api/songs/123/play/ HTTP/1.1
   Authorization: Bearer [token]
   ```

2. **Server tiếp nhận request**:

   - API Router định tuyến request đến `SongViewSet.play()`
   - Hệ thống kiểm tra xác thực người dùng qua token
   - Hệ thống truy xuất bài hát với ID tương ứng từ cơ sở dữ liệu

3. **Xử lý trong `SongViewSet.play()`**:

   ```python
   @action(detail=True, methods=['post'])
   def play(self, request, pk=None):
       """Ghi lại lượt phát của bài hát"""
       song = self.get_object()
       song.play_count += 1
       song.save()

       # Lưu lịch sử phát
       SongPlayHistory.objects.create(
           user=request.user,
           song=song,
           played_at=datetime.now()
       )

       return Response({'status': 'play logged'})
   ```

4. **Phản hồi từ server**:
   - Server trả về thông tin cần thiết để phát bài hát
   - Client nhận và xử lý dữ liệu nhạc

## III. Use case phát nhạc từ Playlist

1. **Bước 1: Chọn playlist**

   - Người dùng mở playlist thông qua `/api/playlists/{id}/`
   - Hệ thống kiểm tra quyền truy cập vào playlist (công khai hoặc sở hữu)
   - Playlist và danh sách bài hát được hiển thị

2. **Bước 2: Phát từ playlist**
   - Người dùng có thể:
     - Phát toàn bộ playlist (theo thứ tự hoặc ngẫu nhiên)
     - Chọn một bài hát cụ thể trong playlist để phát
3. **Bước 3: Xử lý phát nhạc**
   - Khi phát từng bài hát trong playlist, quy trình tương tự như phát một bài đơn lẻ
   - Mỗi bài hát được phát sẽ được ghi lại trong lịch sử nghe

## IV. Các tính năng bổ sung khi phát nhạc

### A. Thích bài hát

```http
POST /api/songs/123/like/ HTTP/1.1
Authorization: Bearer [token]
```

### B. Thêm bài hát vào playlist

```http
POST /api/playlists/456/add_song/ HTTP/1.1
Authorization: Bearer [token]
Content-Type: application/json

{
    "song_id": 123
}
```

### C. Bình luận về bài hát

```http
POST /api/comments/ HTTP/1.1
Authorization: Bearer [token]
Content-Type: application/json

{
    "song": 123,
    "content": "Bài hát tuyệt vời!"
}
```

### D. Đánh giá bài hát

```http
POST /api/ratings/ HTTP/1.1
Authorization: Bearer [token]
Content-Type: application/json

{
    "song": 123,
    "rating": 5
}
```

## V. Quy trình tải lên bài hát mới

1. **Bước 1: Chuẩn bị dữ liệu**
   - Người dùng chuẩn bị file âm thanh và thông tin bài hát
2. **Bước 2: Tải lên thông qua API**

   ```http
   POST /api/upload/ HTTP/1.1
   Authorization: Bearer [token]
   Content-Type: multipart/form-data

   {
       "title": "Tên bài hát",
       "artist": "Tên nghệ sĩ",
       "album": "Tên album",
       "duration": 240,
       "audio_file": [file binary data],
       "cover_image": [image binary data],
       "genre": "Pop",
       "lyrics": "Lời bài hát..."
   }
   ```

3. **Bước 3: Xử lý trên server**

   - Server xác thực người dùng
   - Lưu trữ file âm thanh và ảnh bìa
   - Tạo bản ghi Song mới trong database
   - Trả về thông tin bài hát đã tạo

4. **Bước 4: Xác nhận và hiển thị**
   - Client hiển thị thông báo thành công
   - Bài hát mới xuất hiện trong thư viện của người dùng
   - Bài hát có thể được phát ngay lập tức
