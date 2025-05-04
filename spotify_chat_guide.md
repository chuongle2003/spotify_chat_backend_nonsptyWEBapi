# Hướng dẫn sử dụng Spotify Chat API

## Tổng quan

Spotify Chat là một ứng dụng cho phép người dùng kết nối, trò chuyện và chia sẻ nội dung âm nhạc với nhau trong thời gian thực. Hệ thống hỗ trợ nhiều loại tin nhắn khác nhau và tính năng quản lý tin nhắn, giúp tạo ra một không gian trò chuyện an toàn và thú vị.

## Chức năng chính

### 1. Tin nhắn trực tiếp (Direct Messaging)

- **Gửi và nhận tin nhắn văn bản**: Trao đổi nội dung văn bản với người dùng khác
- **Đánh dấu đã đọc**: Theo dõi trạng thái đã đọc của tin nhắn
- **Gửi file đính kèm**: Chia sẻ các loại file như hình ảnh, ghi âm, tài liệu
- **Chia sẻ âm nhạc**: Gửi bài hát, playlist từ Spotify tới người dùng khác

### 2. Kết nối theo dõi (Social Connections)

- **Theo dõi người dùng**: Kết nối với những người dùng khác thông qua tính năng theo dõi
- **Tìm kiếm người dùng**: Tìm bạn bè, nghệ sĩ và người dùng khác
- **Đề xuất kết nối**: Nhận các đề xuất người dùng dựa trên sở thích âm nhạc

### 3. Chat thời gian thực (Real-time Chat)

- **WebSocket**: Kết nối và nhận tin nhắn tức thì không cần refresh trang
- **Chỉ báo đang nhập**: Hiển thị khi người dùng đang nhập tin nhắn
- **Thông báo**: Nhận thông báo khi có tin nhắn mới

### 4. Quản lý nội dung (Content Moderation)

- **Báo cáo tin nhắn**: Báo cáo nội dung không phù hợp
- **Lọc nội dung**: Tự động phát hiện và đánh dấu nội dung có vấn đề
- **Hạn chế chat**: Quản lý người dùng vi phạm quy định

### 5. Trợ lý AI (AI Assistant)

- **Chat thông minh**: Tương tác với trợ lý AI được hỗ trợ bởi Google Gemini
- **Multimodal**: Hỗ trợ cả text và hình ảnh trong tương tác
- **Lịch sử hội thoại**: Lưu trữ và tham chiếu đến các cuộc hội thoại trước đó
- **Ngữ cảnh tùy chỉnh**: Cá nhân hóa trợ lý cho các trường hợp sử dụng khác nhau

## Cấu trúc dữ liệu

### Tin nhắn (Message)

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
  "shared_song": null,
  "shared_playlist": null,
  "attachment": null,
  "image": null,
  "voice_note": null
}
```

### Tin nhắn chia sẻ bài hát (Song Share Message)

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
  "content": "Bạn nghe thử bài này nhé!",
  "timestamp": "2023-11-20T15:35:12Z",
  "is_read": false,
  "message_type": "SONG",
  "shared_song": {
    "id": 789,
    "title": "Tên bài hát",
    "artist": "Tên nghệ sĩ",
    "cover_image": "https://example.com/covers/song.jpg",
    "duration": 180
  },
  "shared_playlist": null,
  "attachment": null,
  "image": null,
  "voice_note": null
}
```

### Báo cáo tin nhắn (Message Report)

```json
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
}
```

### Hạn chế chat (Chat Restriction)

```json
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
}
```

### AI Conversation

```json
{
  "id": 1,
  "title": "Hỏi về cách sử dụng playlist",
  "user": {
    "id": 123,
    "username": "user123"
  },
  "system_context": "Bạn là trợ lý âm nhạc, giúp người dùng tìm hiểu về các tính năng của ứng dụng Spotify Chat",
  "created_at": "2023-11-20T14:30:00Z",
  "updated_at": "2023-11-20T16:45:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Làm thế nào để tạo playlist?",
      "created_at": "2023-11-20T14:30:00Z",
      "has_image": false
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Để tạo playlist, bạn có thể nhấn vào nút 'Tạo playlist mới' ở góc trên bên phải của trang chủ...",
      "created_at": "2023-11-20T14:30:15Z",
      "has_image": false
    }
  ]
}
```

## REST API Endpoints

### API Chat

| Phương thức | Endpoint                             | Mô tả                                     |
| ----------- | ------------------------------------ | ----------------------------------------- |
| GET         | `/api/chat/messages/`                | Lấy danh sách tin nhắn của người dùng     |
| GET         | `/api/chat/messages/{id}/`           | Xem chi tiết tin nhắn                     |
| POST        | `/api/chat/messages/`                | Gửi tin nhắn mới                          |
| GET         | `/api/chat/conversations/`           | Lấy danh sách cuộc trò chuyện             |
| GET         | `/api/chat/conversations/{user_id}/` | Lấy cuộc trò chuyện với người dùng cụ thể |
| POST        | `/api/chat/report-message/`          | Báo cáo tin nhắn vi phạm                  |

### API Kết nối người dùng

| Phương thức | Endpoint                                   | Mô tả                             |
| ----------- | ------------------------------------------ | --------------------------------- |
| GET         | `/api/accounts/social/following/`          | Lấy danh sách người đang theo dõi |
| GET         | `/api/accounts/social/followers/`          | Lấy danh sách người theo dõi      |
| GET         | `/api/accounts/social/search/?q={query}`   | Tìm kiếm người dùng               |
| GET         | `/api/accounts/social/recommendations/`    | Lấy đề xuất người dùng            |
| POST        | `/api/accounts/social/follow/{user_id}/`   | Theo dõi người dùng               |
| POST        | `/api/accounts/social/unfollow/{user_id}/` | Hủy theo dõi người dùng           |

### API Admin

| Phương thức | Endpoint                              | Mô tả                            |
| ----------- | ------------------------------------- | -------------------------------- |
| GET         | `/api/chat/admin/messages/`           | Lấy danh sách tất cả tin nhắn    |
| GET         | `/api/chat/admin/messages/{id}/`      | Xem chi tiết tin nhắn            |
| GET         | `/api/chat/admin/reports/`            | Xem danh sách báo cáo tin nhắn   |
| GET         | `/api/chat/admin/reports/{id}/`       | Xem chi tiết báo cáo             |
| PUT         | `/api/chat/admin/reports/{id}/`       | Cập nhật trạng thái báo cáo      |
| GET         | `/api/chat/admin/reports/statistics/` | Thống kê báo cáo tin nhắn        |
| GET         | `/api/chat/admin/reports/pending/`    | Xem báo cáo đang chờ xử lý       |
| GET         | `/api/chat/admin/restrictions/`       | Xem tất cả hạn chế chat          |
| POST        | `/api/chat/admin/restrictions/`       | Tạo hạn chế chat mới             |
| PUT         | `/api/chat/admin/restrictions/{id}/`  | Cập nhật hạn chế chat            |
| GET         | `/api/chat/admin/stats/{user_id}/`    | Xem thống kê chat của người dùng |

### API AI Assistant

| Phương thức | Endpoint                                  | Mô tả                                     |
| ----------- | ----------------------------------------- | ----------------------------------------- |
| GET         | `/api/v1/ai/conversations/`               | Lấy danh sách hội thoại AI của người dùng |
| POST        | `/api/v1/ai/conversations/`               | Tạo hội thoại AI mới                      |
| GET         | `/api/v1/ai/conversations/{id}/`          | Xem chi tiết hội thoại AI                 |
| DELETE      | `/api/v1/ai/conversations/{id}/`          | Xóa hội thoại AI                          |
| GET         | `/api/v1/ai/conversations/{id}/messages/` | Lấy tin nhắn trong hội thoại              |
| DELETE      | `/api/v1/ai/conversations/{id}/clear/`    | Xóa tất cả tin nhắn trong hội thoại       |
| POST        | `/api/v1/ai/generate-text/`               | Tạo phản hồi văn bản từ AI                |
| POST        | `/api/v1/ai/generate-multimodal/`         | Tạo phản hồi từ văn bản + hình ảnh        |
| GET         | `/api/v1/ai/system-instructions/`         | Lấy danh sách hướng dẫn hệ thống có sẵn   |
| GET         | `/api/v1/ai/system-prompts/`              | Lấy danh sách prompt hệ thống             |

## WebSocket API

### Kết nối WebSocket cho Chat

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

### Kết nối WebSocket cho AI Assistant

Để kết nối WebSocket cho AI Assistant:

```javascript
// Kết nối đến cuộc hội thoại AI
const socket = new WebSocket(
  `wss://spotifybackend.shop/ws/ai/chat/${conversationId}/`
);

// Lắng nghe phản hồi từ AI
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "message") {
    console.log("Phản hồi từ AI:", data.message);
  } else if (data.type === "typing") {
    console.log("AI đang nhập...");
  }
};

// Gửi tin nhắn đến AI
socket.send(
  JSON.stringify({
    type: "message",
    message: "Làm thế nào để tạo playlist?",
    system_context:
      "Bạn là trợ lý âm nhạc, giúp người dùng tìm hiểu về các tính năng của ứng dụng",
  })
);
```

### Cấu trúc dữ liệu WebSocket

#### Gửi tin nhắn Chat

```json
{
  "message": "Nội dung tin nhắn"
}
```

#### Nhận tin nhắn Chat

```json
{
  "type": "message",
  "message": "Nội dung tin nhắn",
  "sender": 123,
  "sender_name": "user123",
  "timestamp": "2023-11-20T15:35:12Z"
}
```

#### Chỉ báo đang nhập

```json
{
  "type": "typing",
  "is_typing": true,
  "user_id": 123
}
```

#### Gửi tin nhắn đến AI Assistant

```json
{
  "type": "message",
  "message": "Làm thế nào để chia sẻ bài hát với bạn bè?",
  "conversation_id": 1,
  "system_context": "Bạn là trợ lý âm nhạc chuyên nghiệp"
}
```

#### Nhận phản hồi từ AI Assistant

```json
{
  "type": "message",
  "message": "Để chia sẻ bài hát với bạn bè, bạn có thể làm theo các bước sau...",
  "role": "assistant",
  "conversation_id": 1
}
```

## Quy trình sử dụng

### 1. Gửi tin nhắn văn bản

1. Gửi POST request đến `/api/chat/messages/` với dữ liệu:
   ```json
   {
     "receiver": 456,
     "content": "Nội dung tin nhắn"
   }
   ```
2. Hoặc sử dụng WebSocket để gửi tin nhắn theo thời gian thực.

### 2. Chia sẻ bài hát

1. Gửi POST request đến `/api/chat/messages/` với dữ liệu:
   ```json
   {
     "receiver": 456,
     "content": "Nghe thử bài này nhé!",
     "shared_song": 789
   }
   ```

### 3. Báo cáo tin nhắn vi phạm

1. Gửi POST request đến `/api/chat/report-message/` với dữ liệu:
   ```json
   {
     "message": 123,
     "reason": "INAPPROPRIATE",
     "description": "Nội dung tin nhắn vi phạm quy định"
   }
   ```

### 4. Xem lịch sử trò chuyện

1. Gửi GET request đến `/api/chat/conversations/{user_id}/` để xem cuộc trò chuyện với một người dùng cụ thể.

### 5. Tương tác với AI Assistant

1. Tạo cuộc hội thoại mới:

   ```json
   {
     "title": "Hỏi về cách sử dụng playlist",
     "system_context": "Bạn là trợ lý âm nhạc, giúp người dùng tìm hiểu về các tính năng của ứng dụng"
   }
   ```

2. Gửi tin nhắn và nhận phản hồi:

   ```json
   {
     "prompt": "Làm thế nào để tạo playlist?",
     "conversation_id": 1,
     "system_context": "Bạn là trợ lý âm nhạc"
   }
   ```

3. Gửi hình ảnh và tin nhắn:

   ```
   POST /api/v1/ai/generate-multimodal/
   Content-Type: multipart/form-data

   prompt: "Phân tích bài hát trong ảnh này"
   image: [file_data]
   conversation_id: 1
   ```

## Lưu ý phát triển

1. **Xác thực**: Tất cả API đều yêu cầu xác thực JWT.
2. **Hạn chế**: Người dùng bị hạn chế sẽ không thể gửi tin nhắn.
3. **Rate limiting**: API có giới hạn số lượng request trong một khoảng thời gian nhất định.
4. **WebSocket**: Đảm bảo xử lý các trường hợp mất kết nối và tự động kết nối lại.
5. **AI Rate limits**: API AI Assistant có giới hạn số lượng request dựa trên hạn mức của Gemini API.

## Xử lý lỗi

Các mã lỗi phổ biến:

- `400 Bad Request`: Dữ liệu gửi đi không hợp lệ
- `401 Unauthorized`: Chưa xác thực hoặc token hết hạn
- `403 Forbidden`: Không có quyền truy cập
- `404 Not Found`: Không tìm thấy tài nguyên
- `429 Too Many Requests`: Vượt quá giới hạn rate limiting
