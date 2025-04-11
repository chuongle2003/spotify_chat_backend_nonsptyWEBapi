# Ví dụ sử dụng API

## Xác thực

### Đăng nhập (Lấy token)

```bash
curl -X POST http://domain/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

Phản hồi:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Làm mới token

```bash
curl -X POST http://domain/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}'
```

## Quản lý người dùng

### Đăng ký tài khoản mới

```bash
curl -X POST http://domain/api/accounts/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "securepassword123",
    "password2": "securepassword123"
  }'
```

### Xem thông tin cá nhân

```bash
curl -X GET http://domain/api/accounts/users/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Cập nhật thông tin cá nhân

```bash
curl -X PATCH http://domain/api/accounts/users/1/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "I love music!",
    "avatar": null
  }'
```

## Music API

### Tìm kiếm bài hát

```bash
curl -X GET "http://domain/api/music/songs/search/?q=love" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Tạo Playlist mới

```bash
curl -X POST http://domain/api/music/playlists/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Favorite Songs",
    "description": "A collection of my favorite songs",
    "is_public": true
  }'
```

### Thêm bài hát vào Playlist

```bash
curl -X POST http://domain/api/music/playlists/1/add_song/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "song_id": 5
  }'
```

### Upload bài hát mới

```bash
curl -X POST http://domain/api/music/upload/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -F "title=New Song" \
  -F "artist=Artist Name" \
  -F "album=Album Name" \
  -F "genre=Pop" \
  -F "audio_file=@/path/to/song.mp3" \
  -F "cover_image=@/path/to/cover.jpg"
```

### Nghe bài hát (ghi nhận lượt nghe)

```bash
curl -X POST http://domain/api/music/songs/1/play/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Thích/Bỏ thích bài hát

```bash
curl -X POST http://domain/api/music/songs/1/like/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Xem bài hát đang thịnh hành

```bash
curl -X GET http://domain/api/music/songs/trending/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Xem đề xuất bài hát

```bash
curl -X GET http://domain/api/music/songs/recommended/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## Chat API

### Gửi tin nhắn mới

```bash
curl -X POST http://domain/api/chat/messages/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": 2,
    "content": "Hello, how are you?",
    "image": null
  }'
```

### Xem cuộc trò chuyện với một người

```bash
curl -X GET http://domain/api/chat/conversations/2/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Xem danh sách cuộc trò chuyện

```bash
curl -X GET http://domain/api/chat/conversations/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## WebSocket Chat

Kết nối WebSocket cho chat real-time:

```javascript
// JavaScript client-side example
const roomName = "chat_1_2"; // chat giữa user 1 và user 2
const chatSocket = new WebSocket(
  "ws://" + window.location.host + "/ws/chat/" + roomName + "/"
);

chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  console.log("Message:", data);
  // Hiển thị tin nhắn lên UI
};

chatSocket.onclose = function (e) {
  console.error("Chat socket closed unexpectedly");
};

// Gửi tin nhắn
document.querySelector("#chat-input").onkeyup = function (e) {
  if (e.keyCode === 13) {
    // enter key
    const messageInputDom = document.querySelector("#chat-input");
    const message = messageInputDom.value;
    chatSocket.send(
      JSON.stringify({
        message: message,
        sender: userId,
        receiver: otherUserId,
      })
    );
    messageInputDom.value = "";
  }
};
```
