# Spotify Chat Backend - Hướng dẫn sử dụng

## Tổng quan

Hệ thống Spotify Chat Backend là một nền tảng chat với các API RESTful và kết nối WebSocket để tạo điều kiện giao tiếp giữa người dùng. Hệ thống bao gồm chức năng quản lý người dùng, kết nối và trò chuyện.

## Cấu trúc API

Tất cả các API REST được cấu trúc theo định dạng:

```
/api/<tài nguyên>/[<id>/][<hành động>/]
```

Các kết nối WebSocket được cấu trúc theo định dạng:

```
/ws/chat/<định danh>/
```

## Xác thực

Hệ thống sử dụng xác thực JWT:

1. **Đăng nhập và lấy token**:

   ```
   POST /api/token/
   {
     "username": "tên_người_dùng",
     "password": "mật_khẩu"
   }
   ```

   Phản hồi:

   ```json
   {
     "access": "token_truy_cập_jwt",
     "refresh": "token_làm_mới_jwt"
   }
   ```

2. **Làm mới token**:

   ```
   POST /api/token/refresh/
   {
     "refresh": "token_làm_mới_của_bạn"
   }
   ```

3. **Đăng xuất**:
   ```
   POST /api/accounts/logout/
   {
     "refresh": "token_làm_mới_của_bạn"
   }
   ```

Đối với tất cả các API khác, hãy bao gồm tiêu đề xác thực:

```
Authorization: Bearer token_truy_cập_jwt
```

## Hệ thống Chat

### Kết nối WebSocket

Điểm đầu cuối WebSocket cho chat:

```
ws://domain/ws/chat/<tên_người_dùng_nhận>/
```

hoặc với xác thực thông qua tham số truy vấn:

```
ws://domain/ws/chat/<tên_người_dùng_nhận>/?token=token_truy_cập_jwt
```

Trong đó `<tên_người_dùng_nhận>` là tên người dùng của người mà bạn muốn trò chuyện.

### Cải tiến kết nối tự động

Hệ thống hiện đã được cải tiến để tự động tạo và quản lý kết nối giữa người dùng:

1. Khi người dùng kết nối với WebSocket, hệ thống sẽ **tự động tạo hoặc khôi phục kết nối** giữa hai người dùng nếu nó chưa tồn tại.
2. Không cần phải gửi yêu cầu kết nối và chờ chấp nhận trước khi bắt đầu trò chuyện.
3. Người dùng có thể trò chuyện ngay lập tức với bất kỳ người dùng nào trong hệ thống.

### Định dạng tin nhắn WebSocket

**Gửi tin nhắn văn bản**:

```json
{
  "type": "message",
  "message": "Nội dung tin nhắn",
  "username": "tên_người_dùng_của_bạn"
}
```

**Chỉ báo đang nhập**:

```json
{
  "type": "typing",
  "is_typing": true
}
```

**Đánh dấu đã đọc**:

```json
{
  "type": "read"
}
```

### Xử lý tin nhắn nhận được

**Tin nhắn văn bản**:

```json
{
  "type": "message",
  "message": "Nội dung tin nhắn",
  "username": "tên_người_dùng_gửi",
  "timestamp": "2023-10-10T12:34:56.789Z",
  "message_id": 123
}
```

**Chỉ báo đang nhập**:

```json
{
  "type": "typing",
  "username": "tên_người_dùng",
  "is_typing": true/false
}
```

**Xác nhận đã đọc**:

```json
{
  "type": "read",
  "username": "tên_người_dùng",
  "timestamp": "2023-10-10T12:34:56.789Z"
}
```

**Trạng thái người dùng**:

```json
{
  "type": "status",
  "username": "tên_người_dùng",
  "status": "online/offline"
}
```

## API Chat

### Danh sách tin nhắn

```
GET /api/chat/history/<tên_người_dùng>/
```

Lấy lịch sử tin nhắn giữa người dùng hiện tại và người dùng được chỉ định.

### Đếm tin nhắn chưa đọc

```
GET /api/chat/unread/count/
```

Đếm số tin nhắn chưa đọc cho người dùng hiện tại, với chi tiết theo người gửi.

### Đánh dấu đã đọc

```
POST /api/chat/mark-read/<tên_người_dùng>/
```

Đánh dấu tất cả tin nhắn từ người dùng được chỉ định là đã đọc.

### Danh sách cuộc trò chuyện

```
GET /api/chat/conversations/
```

Liệt kê tất cả các cuộc trò chuyện mà người dùng hiện tại đã tham gia, bao gồm tin nhắn mới nhất và số lượng chưa đọc.

### Cuộc trò chuyện gần đây

```
GET /api/chat/recent-conversations/?limit=10
```

Lấy các cuộc trò chuyện gần đây nhất, giới hạn theo số lượng chỉ định.

## Quản lý kết nối người dùng

Mặc dù hệ thống hiện tự động tạo kết nối khi kết nối WebSocket, bạn vẫn có thể sử dụng các API sau để quản lý kết nối:

### Danh sách kết nối

```
GET /api/accounts/connections/users/
```

Liệt kê tất cả các kết nối của người dùng hiện tại.

### Gửi yêu cầu kết nối

```
POST /api/accounts/connections/request/<user_id>/
```

### Chấp nhận yêu cầu kết nối

```
POST /api/accounts/connections/accept/<connection_id>/
```

### Từ chối yêu cầu kết nối

```
POST /api/accounts/connections/decline/<connection_id>/
```

### Chặn người dùng

```
POST /api/accounts/connections/block/<user_id>/
```

### Bỏ chặn người dùng

```
POST /api/accounts/connections/unblock/<user_id>/
```

## Luồng làm việc chung

1. Đăng nhập và lấy token JWT
2. Sử dụng token này để xác thực tất cả các API REST và kết nối WebSocket
3. Kết nối với WebSocket chat để bắt đầu trò chuyện với người dùng khác
4. Gửi và nhận tin nhắn theo thời gian thực
5. Sử dụng API REST để quản lý cuộc trò chuyện, đánh dấu tin nhắn là đã đọc và lấy lịch sử tin nhắn

## Chú ý triển khai

- Hệ thống tự động tạo kết nối giữa hai người dùng khi một người cố gắng kết nối với người còn lại qua WebSocket.
- Chức năng chỉ báo đang nhập và trạng thái online/offline cung cấp trải nghiệm người dùng phong phú hơn.
- Xử lý đọc tin nhắn được tích hợp vào cả API REST và WebSocket để linh hoạt.
