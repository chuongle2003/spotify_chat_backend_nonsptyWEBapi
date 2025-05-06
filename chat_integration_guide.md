# Hướng dẫn tích hợp chức năng chat

## Giới thiệu

Tài liệu này mô tả cách tích hợp và sử dụng hệ thống chat trong ứng dụng của bạn. Hệ thống chat sử dụng kết hợp REST API và WebSocket để cung cấp trải nghiệm chat thời gian thực.

## Xác thực

Mọi API và kết nối WebSocket đều yêu cầu xác thực bằng JWT token:

```
Authorization: Bearer <your_token>
```

## API Endpoints

### 1. Lấy danh sách cuộc trò chuyện

```
GET /api/v1/chats/
```

**Response:**

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "other_user": {
        "id": 2,
        "username": "user2",
        "full_name": "User 2"
      },
      "last_message": {
        "content": "Hello, how are you?",
        "timestamp": "2023-08-01T12:30:45Z",
        "is_read": true
      },
      "unread_count": 0
    },
    {
      "id": 2,
      "other_user": {
        "id": 3,
        "username": "user3",
        "full_name": "User 3"
      },
      "last_message": {
        "content": "Let's meet tomorrow",
        "timestamp": "2023-08-02T10:15:30Z",
        "is_read": false
      },
      "unread_count": 3
    }
  ]
}
```

### 2. Lấy lịch sử tin nhắn

```
GET /api/v1/messages/{username}/?page=1
```

**Response:**

```json
{
  "count": 25,
  "next": "/api/v1/messages/{username}/?page=2",
  "previous": null,
  "results": [
    {
      "id": 101,
      "content": "Hi there!",
      "sender": "user1",
      "receiver": "user2",
      "timestamp": "2023-08-02T14:30:10Z",
      "is_read": true
    },
    {
      "id": 102,
      "content": "Hello! How are you?",
      "sender": "user2",
      "receiver": "user1",
      "timestamp": "2023-08-02T14:31:05Z",
      "is_read": true
    }
  ]
}
```

### 3. Đánh dấu tin nhắn đã đọc

```
POST /api/v1/messages/{message_id}/read/
```

**Response:**

```json
{
  "success": true,
  "message": "Đã đánh dấu là đã đọc"
}
```

## Kết nối WebSocket

### 1. Thiết lập kết nối

Mẫu URL WebSocket:

```
ws://your-domain/ws/chat/{username}/
```

Ví dụ: Để chat với user có username là "user2":

```
ws://your-domain/ws/chat/user2/
```

### 2. Cách truyền token:

Khi kết nối, bạn cần gửi request với header Authorization:

```javascript
const socket = new WebSocket(wsUrl);

// Sẽ không hoạt động trực tiếp với WebSocket
// Cần một giải pháp khác:
const socket = new WebSocket(wsUrl, [], {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

// Cách 2: Sử dụng middleware của backend
// Token được trích xuất từ query params hoặc headers
// Vì vậy có thể thêm vào URL
const socket = new WebSocket(`${wsUrl}?token=${token}`);
```

### 3. Định dạng tin nhắn gửi đi

```json
{
  "message": "Nội dung tin nhắn"
}
```

### 4. Định dạng tin nhắn nhận về

**Tin nhắn thông thường:**

```json
{
  "type": "message",
  "message": "Nội dung tin nhắn",
  "username": "user2",
  "timestamp": "2023-08-02T15:45:30Z"
}
```

**Thông báo lỗi:**

```json
{
  "type": "error",
  "code": "INVALID_MESSAGE",
  "message": "Tin nhắn không hợp lệ"
}
```

**Thông báo thành công:**

```json
{
  "type": "success",
  "code": "CONNECTED",
  "message": "Kết nối WebSocket thành công"
}
```

## Mã lỗi

| Mã              | Mô tả                                  |
| --------------- | -------------------------------------- |
| UNAUTHORIZED    | Chưa đăng nhập hoặc token không hợp lệ |
| USER_NOT_FOUND  | Không tìm thấy người dùng              |
| RESTRICTED      | Bị hạn chế tính năng chat              |
| INVALID_MESSAGE | Tin nhắn không hợp lệ                  |
| INTERNAL_ERROR  | Lỗi hệ thống                           |

## Ví dụ tích hợp đầy đủ

```javascript
class ChatService {
  constructor(baseUrl, apiUrl, token) {
    this.baseUrl = baseUrl;
    this.apiUrl = apiUrl;
    this.token = token;
    this.socket = null;
    this.onMessageCallback = null;
    this.onErrorCallback = null;
    this.onConnectCallback = null;
  }

  // Kết nối WebSocket
  connect(username) {
    const wsUrl = `${this.baseUrl}/ws/chat/${username}/`;

    // Kết nối với WebSocket server
    this.socket = new WebSocket(`${wsUrl}?token=${this.token}`);

    this.socket.onopen = () => {
      console.log("WebSocket kết nối thành công");
      if (this.onConnectCallback) this.onConnectCallback();
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "message":
          if (this.onMessageCallback) this.onMessageCallback(data);
          break;
        case "error":
          if (this.onErrorCallback) this.onErrorCallback(data);
          break;
        case "success":
          console.log("Success:", data.message);
          break;
      }
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      if (this.onErrorCallback)
        this.onErrorCallback({
          code: "CONNECTION_ERROR",
          message: "Lỗi kết nối",
        });
    };

    this.socket.onclose = () => {
      console.log("WebSocket đã đóng");
      // Tự động kết nối lại sau 5 giây
      setTimeout(() => this.connect(username), 5000);
    };
  }

  // Gửi tin nhắn
  sendMessage(message) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket chưa kết nối");
    }

    this.socket.send(
      JSON.stringify({
        message: message,
      })
    );
  }

  // Lấy lịch sử tin nhắn
  async getMessages(username, page = 1) {
    const response = await fetch(
      `${this.apiUrl}/messages/${username}/?page=${page}`,
      {
        headers: {
          Authorization: `Bearer ${this.token}`,
          "Content-Type": "application/json",
        },
      }
    );

    return await response.json();
  }

  // Đánh dấu đã đọc
  async markAsRead(messageId) {
    const response = await fetch(`${this.apiUrl}/messages/${messageId}/read/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
      },
    });

    return await response.json();
  }

  // Lấy danh sách cuộc trò chuyện
  async getChats() {
    const response = await fetch(`${this.apiUrl}/chats/`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
      },
    });

    return await response.json();
  }

  // Đăng ký callback
  onMessage(callback) {
    this.onMessageCallback = callback;
  }

  onError(callback) {
    this.onErrorCallback = callback;
  }

  onConnect(callback) {
    this.onConnectCallback = callback;
  }
}
```

## Sử dụng ChatService

```javascript
// Khởi tạo
const chatService = new ChatService(
  "ws://your-domain",
  "http://your-domain/api/v1",
  "your_jwt_token"
);

// Đăng ký handler
chatService.onMessage((data) => {
  // Hiển thị tin nhắn
  displayMessage({
    content: data.message,
    sender: data.username,
    timestamp: data.timestamp,
  });
});

chatService.onError((error) => {
  // Hiển thị lỗi
  showError(error.message);
});

chatService.onConnect(() => {
  // UI hiển thị đã kết nối
  updateConnectionStatus("connected");
});

// Kết nối với người dùng 'user2'
chatService.connect("user2");

// Hiển thị tin nhắn cũ
async function loadMessages() {
  const messages = await chatService.getMessages("user2");
  for (const msg of messages.results) {
    displayMessage(msg);
  }
}

// Gửi tin nhắn
function sendMessage() {
  const input = document.getElementById("message-input");
  chatService.sendMessage(input.value);
  input.value = "";
}
```

## Xử lý lỗi

Luôn xử lý các trường hợp lỗi phổ biến:

1. Mất kết nối - tự động kết nối lại
2. Token hết hạn - chuyển hướng đến trang đăng nhập
3. Người dùng không tồn tại - hiển thị thông báo
4. Lỗi định dạng tin nhắn - kiểm tra trước khi gửi

## Tối ưu hiệu suất

1. Sử dụng phân trang khi tải tin nhắn cũ
2. Sử dụng debounce khi người dùng đang nhập
3. Tải tin nhắn mới nhất trước, sau đó tải lịch sử
4. Lưu cache tin nhắn để giảm số lượng request

## Lưu ý về bảo mật

1. Luôn sử dụng HTTPS và WSS (WebSocket Secure)
2. Không lưu token trong localStorage, sử dụng httpOnly cookies
3. Validate dữ liệu trước khi hiển thị để tránh XSS
4. Không bao giờ tin tưởng dữ liệu từ client
