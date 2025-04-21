# Chi Tiết API Endpoints

## 1. Xác thực (Authentication)

### 1.1 Đăng nhập

- **Endpoint**: `POST /api/auth/token/`
- **Mô tả**: Đăng nhập và nhận JWT token
- **Request Body**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access": "string (JWT token)",
    "refresh": "string (Refresh token)"
  }
  ```
- **Lỗi thường gặp**:
  - 401: Sai thông tin đăng nhập
  - 400: Thiếu thông tin

### 1.2 Làm mới Token

- **Endpoint**: `POST /api/auth/token/refresh/`
- **Mô tả**: Làm mới access token bằng refresh token
- **Request Body**:
  ```json
  {
    "refresh": "string (Refresh token)"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access": "string (JWT token mới)"
  }
  ```
- **Lỗi thường gặp**:
  - 401: Refresh token không hợp lệ
  - 400: Thiếu refresh token

### 1.3 Đăng xuất

- **Endpoint**: `POST /api/auth/logout/`
- **Mô tả**: Đăng xuất và vô hiệu hóa refresh token
- **Headers**:
  ```
  Authorization: Bearer {access_token}
  ```
- **Request Body**:
  ```json
  {
    "refresh": "string (Refresh token)"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "message": "Successfully logged out"
  }
  ```
- **Lỗi thường gặp**:
  - 401: Token không hợp lệ
  - 400: Thiếu refresh token

## 2. Quản lý Tài khoản (Account Management)

### 2.1 Đăng ký

- **Endpoint**: `POST /api/accounts/auth/register/`
- **Mô tả**: Đăng ký tài khoản mới
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string",
    "first_name": "string",
    "last_name": "string"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "integer",
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string"
  }
  ```
- **Lỗi thường gặp**:
  - 400: Username/email đã tồn tại
  - 400: Password không đủ mạnh

### 2.2 Thông tin người dùng

- **Endpoint**: `GET /api/accounts/profile/me/`
- **Mô tả**: Lấy thông tin người dùng hiện tại
- **Headers**:
  ```
  Authorization: Bearer {access_token}
  ```
- **Response (200 OK)**:
  ```json
  {
    "id": "integer",
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "profile": {
      "avatar": "string (URL)",
      "bio": "string"
    }
  }
  ```

### 2.3 Cập nhật thông tin

- **Endpoint**: `PATCH /api/accounts/profile/me/`
- **Mô tả**: Cập nhật thông tin người dùng
- **Headers**:
  ```
  Authorization: Bearer {access_token}
  ```
- **Request Body**:
  ```json
  {
    "first_name": "string",
    "last_name": "string",
    "profile": {
      "bio": "string"
    }
  }
  ```

## 3. Âm nhạc (Music)

### 3.1 Quản lý Bài hát

- **Danh sách bài hát**:

  - `GET /api/music/songs/`
  - Trả về danh sách bài hát
  - Có thể filter theo thể loại, nghệ sĩ

- **Chi tiết bài hát**:

  - `GET /api/music/songs/{id}/`
  - Trả về thông tin chi tiết bài hát

- **Tìm kiếm**:
  - `GET /api/music/songs/search/?q={query}`
  - Tìm kiếm bài hát theo tên, nghệ sĩ

### 3.2 Quản lý Playlist

- **Tạo playlist**:

  - `POST /api/music/playlists/`
  - Request Body:
    ```json
    {
      "name": "string",
      "description": "string",
      "is_public": "boolean"
    }
    ```

- **Thêm bài hát vào playlist**:
  - `POST /api/music/playlists/{id}/add_song/`
  - Request Body:
    ```json
    {
      "song_id": "integer"
    }
    ```

### 3.3 Tương tác

- **Like bài hát**:

  - `POST /api/music/songs/{id}/like/`
  - Thích/bỏ thích bài hát

- **Bình luận**:
  - `POST /api/music/comments/`
  - Request Body:
    ```json
    {
      "song_id": "integer",
      "content": "string"
    }
    ```

## 4. Chat

### 4.1 Tin nhắn

- **Gửi tin nhắn**:

  - `POST /api/chat/messages/`
  - Request Body:
    ```json
    {
      "receiver_id": "integer",
      "content": "string"
    }
    ```

- **Danh sách tin nhắn**:
  - `GET /api/chat/messages/`
  - Query params:
    - `conversation_id`: ID cuộc trò chuyện
    - `limit`: Số tin nhắn tối đa
    - `offset`: Vị trí bắt đầu

### 4.2 Cuộc trò chuyện

- **Danh sách cuộc trò chuyện**:

  - `GET /api/chat/conversations/`
  - Trả về danh sách cuộc trò chuyện của người dùng

- **Tin nhắn với người dùng**:
  - `GET /api/chat/conversations/{user_id}/`
  - Trả về tin nhắn với người dùng cụ thể

## 5. WebSocket

### 5.1 Chat Real-time

- **Endpoint**: `ws://{domain}/ws/chat/{room_name}/`
- **Kết nối**:
  ```javascript
  const socket = new WebSocket("ws://domain/ws/chat/room1/");
  socket.onmessage = function (e) {
    console.log("Message:", e.data);
  };
  ```
- **Gửi tin nhắn**:
  ```javascript
  socket.send(
    JSON.stringify({
      type: "message",
      content: "Hello!",
    })
  );
  ```

## 6. Công khai (Public)

### 6.1 Tìm kiếm công khai

- **Endpoint**: `GET /api/music/public/search/?q={query}`
- **Mô tả**: Tìm kiếm bài hát, playlist công khai
- **Response**:
  ```json
  {
    "songs": [],
    "playlists": [],
    "artists": []
  }
  ```

### 6.2 Playlist công khai

- **Endpoint**: `GET /api/music/public/playlists/`
- **Mô tả**: Lấy danh sách playlist công khai
- **Query params**:
  - `limit`: Số playlist tối đa
  - `offset`: Vị trí bắt đầu
  - `sort`: Cách sắp xếp (popular, latest)

## 7. Tài liệu API

### 7.1 Swagger UI

- **Endpoint**: `GET /api/docs/swagger/`
- **Mô tả**: Giao diện Swagger để test API

### 7.2 ReDoc

- **Endpoint**: `GET /api/docs/redoc/`
- **Mô tả**: Tài liệu API chi tiết

## 8. Lưu ý khi sử dụng

1. **Xác thực**:

   - Sử dụng JWT token trong header `Authorization: Bearer {token}`
   - Token hết hạn sau 1 giờ
   - Sử dụng refresh token để lấy token mới

2. **Rate Limiting**:

   - Tối đa 100 requests/phút cho mỗi IP
   - Tối đa 5 requests/phút cho các endpoint xác thực

3. **Error Handling**:

   - Tất cả lỗi trả về format:
     ```json
     {
       "error": "string",
       "message": "string",
       "status_code": "integer"
     }
     ```

4. **Pagination**:
   - Các endpoint trả về danh sách đều hỗ trợ phân trang
   - Query params: `limit`, `offset`
   - Response format:
     ```json
     {
       "count": "integer",
       "next": "string (URL)",
       "previous": "string (URL)",
       "results": []
     }
     ```
