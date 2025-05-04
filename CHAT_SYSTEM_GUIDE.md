# Hướng dẫn sử dụng hệ thống Chat trong Spotify Clone

## Giới thiệu

Hệ thống Chat của Spotify Clone cho phép người dùng kết nối, trò chuyện và chia sẻ âm nhạc với nhau. Đây là nơi người dùng có thể tìm kiếm bạn bè có cùng sở thích âm nhạc, theo dõi và trò chuyện với họ, tạo nên một cộng đồng âm nhạc sôi động.

## Tính năng chính

### 1. Kết nối người dùng

- **Theo dõi người dùng**: Theo dõi những người dùng có cùng sở thích âm nhạc
- **Hiển thị người theo dõi**: Xem ai đang theo dõi bạn
- **Tìm kiếm người dùng**: Tìm bạn bè theo tên hoặc username
- **Gợi ý kết nối**: Nhận đề xuất người dùng dựa trên sở thích âm nhạc tương đồng

### 2. Trò chuyện thời gian thực

- **Chat trực tiếp**: Gửi và nhận tin nhắn ngay lập tức
- **Chia sẻ bài hát**: Gửi bài hát yêu thích cho bạn bè
- **Xem cuộc trò chuyện**: Quản lý và xem lại lịch sử tin nhắn
- **Thông báo**: Nhận thông báo khi có tin nhắn mới

### 3. Chia sẻ âm nhạc

- **Chia sẻ bài hát**: Gửi bài hát đang nghe cho bạn bè
- **Xem ảnh bìa**: Hiển thị ảnh bìa bài hát được chia sẻ
- **Phát trực tiếp**: Nghe thử bài hát được chia sẻ ngay trong chat

## Cách sử dụng

### Kết nối với người dùng khác

1. **Tìm người dùng**:

   - Sử dụng thanh tìm kiếm ở phần Chat
   - Gõ tên hoặc username người dùng bạn muốn tìm
   - Nhận các gợi ý người dùng có sở thích âm nhạc tương tự

2. **Theo dõi người dùng**:

   - Nhấn vào nút "Theo dõi" trên trang profile của người dùng
   - Người dùng sẽ xuất hiện trong danh sách người bạn đang theo dõi

3. **Quản lý kết nối**:
   - Xem danh sách người bạn đang theo dõi
   - Xem danh sách người đang theo dõi bạn
   - Hủy theo dõi nếu muốn

### Trò chuyện với người dùng

1. **Bắt đầu cuộc trò chuyện**:

   - Nhấn vào biểu tượng chat trên trang profile người dùng
   - Chọn người dùng từ danh sách đang theo dõi
   - Gõ tin nhắn và gửi đi

2. **Chia sẻ bài hát**:

   - Trong khi nghe nhạc, nhấn nút "Chia sẻ"
   - Chọn người dùng để gửi
   - Thêm tin nhắn kèm theo (tùy chọn)
   - Gửi đi

3. **Quản lý cuộc trò chuyện**:
   - Xem danh sách tất cả cuộc trò chuyện
   - Đánh dấu tin nhắn đã đọc
   - Xóa cuộc trò chuyện nếu cần

## API Endpoints

Dưới đây là các API endpoints có thể sử dụng để tích hợp chat vào ứng dụng:

### API Kết nối người dùng

| Phương thức | Endpoint                                      | Mô tả                             |
| ----------- | --------------------------------------------- | --------------------------------- |
| GET         | `/api/v1/accounts/social/following/`          | Lấy danh sách người đang theo dõi |
| GET         | `/api/v1/accounts/social/followers/`          | Lấy danh sách người theo dõi      |
| GET         | `/api/v1/accounts/social/search/?q={query}`   | Tìm kiếm người dùng               |
| GET         | `/api/v1/accounts/social/recommendations/`    | Lấy đề xuất người dùng            |
| POST        | `/api/v1/accounts/social/follow/{user_id}/`   | Theo dõi người dùng               |
| POST        | `/api/v1/accounts/social/unfollow/{user_id}/` | Hủy theo dõi người dùng           |

### API Chat

| Phương thức | Endpoint                                | Mô tả                              |
| ----------- | --------------------------------------- | ---------------------------------- |
| GET         | `/api/v1/chat/conversations/`           | Lấy danh sách cuộc trò chuyện      |
| GET         | `/api/v1/chat/conversations/{user_id}/` | Lấy tin nhắn với người dùng cụ thể |
| GET         | `/api/v1/chat/messages/`                | Lấy tất cả tin nhắn                |
| POST        | `/api/v1/chat/messages/`                | Gửi tin nhắn mới                   |
| GET         | `/api/v1/chat/messages/{id}/`           | Xem chi tiết tin nhắn              |

### WebSocket

Để kết nối WebSocket cho chat thời gian thực:

```javascript
// Kết nối đến phòng chat
const socket = new WebSocket(`wss://spotifybackend.shop/ws/chat/${roomName}/`);

// Lắng nghe tin nhắn
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Tin nhắn mới:", data.message);
};

// Gửi tin nhắn
socket.send(
  JSON.stringify({
    message: "Nội dung tin nhắn",
  })
);
```

## Cấu trúc dữ liệu

### Message (Tin nhắn)

```json
{
  "id": 1,
  "sender": {
    "id": 123,
    "username": "user123",
    "avatar": "https://example.com/avatar.jpg"
  },
  "receiver": {
    "id": 456,
    "username": "user456",
    "avatar": "https://example.com/avatar2.jpg"
  },
  "content": "Chào bạn, bạn khỏe không?",
  "timestamp": "2023-11-20T15:30:45Z",
  "is_read": false,
  "message_type": "TEXT",
  "shared_song": null
}
```

### Shared Song Message (Tin nhắn chia sẻ bài hát)

```json
{
  "id": 2,
  "sender": {
    "id": 123,
    "username": "user123",
    "avatar": "https://example.com/avatar.jpg"
  },
  "receiver": {
    "id": 456,
    "username": "user456",
    "avatar": "https://example.com/avatar2.jpg"
  },
  "content": "Nghe thử bài này đi: Hãy Trao Cho Anh",
  "timestamp": "2023-11-20T15:45:30Z",
  "is_read": false,
  "message_type": "SONG",
  "shared_song": {
    "id": 789,
    "title": "Hãy Trao Cho Anh",
    "artist": "Sơn Tùng M-TP",
    "cover_image": "https://example.com/cover.jpg",
    "audio_file": "https://example.com/song.mp3",
    "duration": 240
  }
}
```

### Conversation (Cuộc trò chuyện)

```json
{
  "other_user": {
    "id": 456,
    "username": "user456",
    "avatar": "https://example.com/avatar2.jpg"
  },
  "last_message": {
    "content": "Nghe thử bài này đi: Hãy Trao Cho Anh",
    "timestamp": "2023-11-20T15:45:30Z",
    "message_type": "SONG"
  },
  "unread_count": 2
}
```

## Lưu ý

1. **Bảo mật**: Tất cả các tin nhắn được mã hóa và chỉ người gửi và người nhận mới có thể xem
2. **Tính khả dụng**: Hệ thống chat hoạt động cả khi online và offline (tin nhắn sẽ được đồng bộ khi online)
3. **Đồng bộ hóa**: Tin nhắn được đồng bộ hóa trên tất cả các thiết bị của người dùng

---

Nếu bạn có bất kỳ câu hỏi nào về hệ thống chat, vui lòng liên hệ với chúng tôi qua support@spotifybackend.shop.
