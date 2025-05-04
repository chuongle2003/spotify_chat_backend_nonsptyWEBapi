# API Guide - Spotify Chat Backend

## Cấu trúc API mới

Tất cả API được tổ chức theo cấu trúc REST chuẩn:

```
/api/v1/<resource>/[<id>/][<action>/]
```

Tất cả WebSocket được tổ chức theo cấu trúc:

```
/ws/v1/<service>/<identifier>/
```

## 1. Xác thực (Authentication)

### Lấy JWT Token

**Request:**

```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "email": "user@gmail.com",
  "password": "password123"
}
```

**Response:**

```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": 123,
    "username": "username",
    "email": "user@gmail.com",
    "avatar": "url_to_avatar",
    "is_admin": false
  }
}
```

### Làm mới Token

**Request:**

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "jwt_refresh_token"
}
```

**Response:**

```json
{
  "access": "new_jwt_access_token"
}
```

### Đăng xuất

**Request:**

```http
POST /api/v1/accounts/logout/
Authorization: Bearer jwt_access_token
Content-Type: application/json

{
  "refresh": "jwt_refresh_token"
}
```

**Response:**

```json
{
  "message": "Successfully logged out"
}
```

## 2. Quản lý Tài khoản (Accounts)

### Lấy danh sách người dùng

**Request:**

```http
GET /api/v1/accounts/user-list/
Authorization: Bearer jwt_access_token
```

### Gợi ý người dùng

**Request:**

```http
GET /api/v1/accounts/user-suggestions/
Authorization: Bearer jwt_access_token
```

### Tìm kiếm người dùng

**Request:**

```http
GET /api/v1/accounts/user-search/?q=search_term
Authorization: Bearer jwt_access_token
```

### Thông tin người dùng hiện tại

**Request:**

```http
GET /api/v1/accounts/users/me/
Authorization: Bearer jwt_access_token
```

## 3. Quản lý Kết nối (Connections)

### Lấy danh sách người dùng đã kết nối

**Request:**

```http
GET /api/v1/accounts/connections/
Authorization: Bearer jwt_access_token
```

### Lấy danh sách yêu cầu kết nối đang chờ

**Request:**

```http
GET /api/v1/accounts/connections/pending/
Authorization: Bearer jwt_access_token
```

### Gửi yêu cầu kết nối

**Request:**

```http
POST /api/v1/accounts/connections/request/{user_id}/
Authorization: Bearer jwt_access_token
```

### Chấp nhận yêu cầu kết nối

**Request:**

```http
POST /api/v1/accounts/connections/accept/{connection_id}/
Authorization: Bearer jwt_access_token
```

### Từ chối yêu cầu kết nối

**Request:**

```http
POST /api/v1/accounts/connections/decline/{connection_id}/
Authorization: Bearer jwt_access_token
```

### Hủy kết nối

**Request:**

```http
POST /api/v1/accounts/connections/remove/{user_id}/
Authorization: Bearer jwt_access_token
```

### Chặn người dùng

**Request:**

```http
POST /api/v1/accounts/connections/block/{user_id}/
Authorization: Bearer jwt_access_token
```

### Kiểm tra quyền chat

**Request:**

```http
GET /api/v1/accounts/chat-permission/{username}/
Authorization: Bearer jwt_access_token
```

**Response:**

```json
{
  "can_chat": true,
  "user_id": 456,
  "username": "other_username"
}
```

## 4. Tin nhắn và Chat (Messages)

### Lấy lịch sử tin nhắn

**Request:**

```http
GET /api/v1/chat/messages/{username}/
Authorization: Bearer jwt_access_token
```

### Lấy số lượng tin nhắn chưa đọc

**Request:**

```http
GET /api/v1/chat/messages/unread/count/
Authorization: Bearer jwt_access_token
```

**Response:**

```json
{
  "total_unread": 10,
  "unread_by_sender": [
    {
      "sender_id": 123,
      "sender_username": "username1",
      "count": 5
    },
    {
      "sender_id": 456,
      "sender_username": "username2",
      "count": 5
    }
  ]
}
```

### Đánh dấu tin nhắn đã đọc

**Request:**

```http
POST /api/v1/chat/messages/mark-read/{username}/
Authorization: Bearer jwt_access_token
```

**Response:**

```json
{
  "success": true,
  "marked_read": 5
}
```

### Lấy danh sách cuộc trò chuyện

**Request:**

```http
GET /api/v1/chat/conversations/
Authorization: Bearer jwt_access_token
```

**Response:**

```json
[
  {
    "user": {
      "id": 123,
      "username": "username1",
      "avatar": "url_to_avatar"
    },
    "latest_message": {
      "content": "Hello there!",
      "timestamp": "2023-05-04T12:34:56Z",
      "is_from_me": false
    },
    "unread_count": 3
  }
]
```

### Lấy cuộc trò chuyện gần đây

**Request:**

```http
GET /api/v1/chat/conversations/recent/?limit=5
Authorization: Bearer jwt_access_token
```

## 5. Hạn chế Chat (Admin)

### Lấy danh sách hạn chế chat

**Request:**

```http
GET /api/v1/chat/restrictions/
Authorization: Bearer jwt_access_token
```

### Hạn chế người dùng

**Request:**

```http
POST /api/v1/chat/users/{user_id}/restrict/
Authorization: Bearer jwt_access_token
Content-Type: application/json

{
  "restriction_type": "TEMPORARY",
  "reason": "Violation of community guidelines",
  "duration_days": 7
}
```

### Hủy hạn chế người dùng

**Request:**

```http
POST /api/v1/chat/users/{user_id}/unrestrict/
Authorization: Bearer jwt_access_token
```

## 6. WebSocket

### Kết nối WebSocket Chat

**URL:**

```
wss://domain/ws/v1/chat/{username}/?token=jwt_access_token
```

### Gửi tin nhắn qua WebSocket

**Định dạng:**

```json
{
  "message": "Hello there!",
  "username": "your_username"
}
```

### Nhận tin nhắn qua WebSocket

**Định dạng:**

```json
{
  "message": "Hello there!",
  "username": "sender_username"
}
```

## Quy trình Thông thường

1. Đăng nhập để lấy token
2. Kiểm tra quyền chat với người dùng khác
3. Kết nối WebSocket để bắt đầu chat
4. Gửi và nhận tin nhắn qua WebSocket
5. Khi offline, lấy lịch sử tin nhắn khi kết nối lại

## Lưu ý

1. API cũ vẫn được duy trì ở `/api/` để đảm bảo tương thích ngược, nhưng sẽ được loại bỏ trong tương lai
2. Tất cả API mới nên sử dụng endpoint `/api/v1/`
3. Tất cả WebSocket mới nên sử dụng endpoint `/ws/v1/`
4. JWT Token nên được gửi trong header `Authorization` dưới dạng `Bearer token`
5. Với WebSocket, token nên được gửi qua URL parameter `?token=jwt_token`
