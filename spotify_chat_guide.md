# Hướng dẫn sử dụng WebSocket Chat API cho Client

## Giới thiệu

Tài liệu này cung cấp hướng dẫn chi tiết về cách kết nối và sử dụng WebSocket Chat API trong ứng dụng Spotify Chat. Các hướng dẫn dành cho lập trình viên frontend muốn tích hợp tính năng chat thời gian thực vào ứng dụng khách.

## Thông tin kết nối

- **Endpoint**: `wss://spotifybackend.shop/ws/chat/{room_name}/`
- **Giao thức**: WebSocket Secure (WSS)
- **Yêu cầu xác thực**: JWT Token

## Xác thực

Tất cả kết nối WebSocket đều yêu cầu xác thực JWT. Bạn có thể cung cấp token theo một trong hai cách:

### 1. Sử dụng Query Parameter

```
wss://spotifybackend.shop/ws/chat/room1/?token=YOUR_JWT_TOKEN
```

### 2. Sử dụng Authorization Header

```
Authorization: Bearer YOUR_JWT_TOKEN
```

> **Lưu ý**: Token JWT phải hợp lệ và chưa hết hạn. Nếu token hết hạn, kết nối sẽ bị từ chối với mã lỗi 403.

## Cập nhật quan trọng về hệ thống kết nối

> **Cập nhật mới**: Bây giờ tất cả người dùng đều có thể chat với nhau mà không cần phải thiết lập kết nối trước. API kết nối vẫn hoạt động như trước đây nhưng không còn bắt buộc để sử dụng chức năng chat.

- API `can-chat-with-user` vẫn hoạt động nhưng luôn trả về `"can_chat": true`
- Người dùng vẫn có thể theo dõi người dùng khác để dễ dàng tìm kiếm trong danh sách liên hệ
- Tính năng gợi ý người dùng vẫn hoạt động bình thường

## Thiết lập kết nối WebSocket

### Ví dụ với JavaScript

```javascript
// Khởi tạo WebSocket với token xác thực
function initializeChatWebSocket(roomName, token) {
  // Kết nối đến WebSocket server với token
  const socket = new WebSocket(
    `wss://spotifybackend.shop/ws/chat/${roomName}/?token=${token}`
  );

  // Xử lý sự kiện khi kết nối được thiết lập
  socket.onopen = function (event) {
    console.log("Kết nối WebSocket đã được thiết lập");
    // Có thể gửi thông báo trạng thái online hoặc đang hoạt động
  };

  // Xử lý sự kiện khi kết nối bị đóng
  socket.onclose = function (event) {
    console.log(`Kết nối WebSocket đã đóng với mã: ${event.code}`);

    // Xử lý các mã lỗi khác nhau
    switch (event.code) {
      case 4001:
        console.error("Người dùng chưa đăng nhập");
        break;
      case 4003:
        console.error("Token không hợp lệ hoặc hết hạn");
        // Thử làm mới token
        break;
      case 4004:
        console.error("Không tìm thấy phòng chat");
        break;
      case 1000:
        console.log("Đóng kết nối bình thường");
        break;
      default:
        console.error("Lỗi không xác định, mã: " + event.code);
    }

    // Thiết lập kết nối lại sau vài giây nếu không phải lỗi nghiêm trọng
    if (![4004].includes(event.code)) {
      setTimeout(() => {
        console.log("Đang thử kết nối lại...");
        initializeChatWebSocket(roomName, token);
      }, 3000);
    }
  };

  // Xử lý lỗi
  socket.onerror = function (error) {
    console.error("Lỗi WebSocket:", error);
  };

  // Xử lý tin nhắn nhận được
  socket.onmessage = function (event) {
    try {
      const data = JSON.parse(event.data);
      // Xử lý tin nhắn
      console.log("Tin nhắn nhận được:", data);
      // Thêm tin nhắn vào giao diện người dùng
      displayMessage(data);
    } catch (e) {
      console.error("Lỗi khi xử lý tin nhắn:", e);
    }
  };

  return socket;
}

// Hiển thị tin nhắn trên giao diện người dùng
function displayMessage(data) {
  // Thêm logic hiển thị tin nhắn tại đây
  // Ví dụ:
  const messageContainer = document.getElementById("messages-container");
  const messageElement = document.createElement("div");
  messageElement.className = `message ${
    data.username === currentUser ? "sent" : "received"
  }`;
  messageElement.innerHTML = `
    <strong>${data.username}</strong>
    <p>${data.message}</p>
  `;
  messageContainer.appendChild(messageElement);
  messageContainer.scrollTop = messageContainer.scrollHeight;
}

// Gửi tin nhắn
function sendMessage(socket, message, username, roomName) {
  // Kiểm tra trạng thái kết nối
  if (socket.readyState !== WebSocket.OPEN) {
    console.error("Kết nối WebSocket không mở. Trạng thái:", socket.readyState);
    return false;
  }

  // Tạo đối tượng tin nhắn
  const messageObj = {
    message: message,
    username: username,
    room: roomName,
  };

  // Gửi tin nhắn
  try {
    socket.send(JSON.stringify(messageObj));
    return true;
  } catch (e) {
    console.error("Lỗi khi gửi tin nhắn:", e);
    return false;
  }
}

// Ví dụ sử dụng
const token = "YOUR_JWT_TOKEN"; // Lấy từ quá trình đăng nhập
const roomName = "room1"; // ID phòng chat hoặc username người nhận
const socket = initializeChatWebSocket(roomName, token);

// Khi người dùng gửi tin nhắn
document.getElementById("send-button").addEventListener("click", function () {
  const messageInput = document.getElementById("message-input");
  const message = messageInput.value.trim();

  if (message) {
    const sent = sendMessage(socket, message, currentUsername, roomName);
    if (sent) {
      messageInput.value = ""; // Xóa input sau khi gửi thành công
    }
  }
});
```

### Ví dụ với React

```jsx
import React, { useState, useEffect, useRef } from "react";

function ChatComponent({ token, roomName, currentUser }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    // Thiết lập kết nối WebSocket
    connectWebSocket();

    // Dọn dẹp khi component unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [roomName, token]);

  const connectWebSocket = () => {
    // Đóng kết nối cũ nếu có
    if (socketRef.current) {
      socketRef.current.close();
    }

    // Tạo kết nối mới
    const socket = new WebSocket(
      `wss://spotifybackend.shop/ws/chat/${roomName}/?token=${token}`
    );

    socket.onopen = () => {
      console.log("WebSocket kết nối thành công");
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prevMessages) => [...prevMessages, data]);
    };

    socket.onclose = (event) => {
      console.log(`WebSocket đóng kết nối với mã: ${event.code}`);

      // Kết nối lại nếu không phải lỗi nghiêm trọng
      if (![4004].includes(event.code)) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log("Đang kết nối lại...");
          connectWebSocket();
        }, 3000);
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocket lỗi:", error);
    };

    socketRef.current = socket;
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !socketRef.current) return;

    const messageObj = {
      message: inputMessage,
      username: currentUser,
      room: roomName,
    };

    if (socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(messageObj));
      setInputMessage("");
    } else {
      console.error("WebSocket không sẵn sàng:", socketRef.current.readyState);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages-list">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${
              msg.username === currentUser ? "sent" : "received"
            }`}
          >
            <div className="message-header">
              <strong>{msg.username}</strong>
            </div>
            <div className="message-body">{msg.message}</div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSendMessage} className="message-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Nhập tin nhắn..."
          className="message-input"
        />
        <button type="submit" className="send-button">
          Gửi
        </button>
      </form>
    </div>
  );
}

export default ChatComponent;
```

## Định dạng dữ liệu

### Gửi tin nhắn

```json
{
  "message": "Xin chào, bạn có khỏe không?",
  "username": "user123",
  "room": "room1"
}
```

| Trường   | Kiểu   | Mô tả                               |
| -------- | ------ | ----------------------------------- |
| message  | string | Nội dung tin nhắn                   |
| username | string | Tên người dùng gửi tin nhắn         |
| room     | string | Phòng chat hoặc người nhận tin nhắn |

### Nhận tin nhắn

```json
{
  "message": "Xin chào, bạn có khỏe không?",
  "username": "user123"
}
```

| Trường   | Kiểu   | Mô tả                       |
| -------- | ------ | --------------------------- |
| message  | string | Nội dung tin nhắn           |
| username | string | Tên người dùng gửi tin nhắn |

## Chỉ báo đang nhập (Typing Indicator)

### Gửi trạng thái đang nhập

```json
{
  "type": "typing",
  "is_typing": true,
  "room": "room1"
}
```

| Trường    | Kiểu    | Mô tả                                |
| --------- | ------- | ------------------------------------ |
| type      | string  | Loại tin nhắn, giá trị là "typing"   |
| is_typing | boolean | true nếu đang nhập, false nếu dừng   |
| room      | string  | Phòng chat hoặc người nhận thông báo |

### Nhận trạng thái đang nhập

```json
{
  "type": "typing",
  "is_typing": true,
  "user_id": 123
}
```

## Mã lỗi WebSocket

| Mã lỗi | Mô tả                      | Xử lý                            |
| ------ | -------------------------- | -------------------------------- |
| 4001   | Người dùng chưa đăng nhập  | Chuyển hướng tới trang đăng nhập |
| 4003   | Token không hợp lệ/hết hạn | Làm mới token và kết nối lại     |
| 4004   | Không tìm thấy phòng chat  | Kiểm tra ID phòng và thử lại     |
| 1000   | Đóng kết nối bình thường   | Có thể thử kết nối lại           |

## Xử lý mất kết nối

Để đảm bảo trải nghiệm người dùng tốt nhất, hãy thực hiện các chiến lược sau khi mất kết nối:

1. **Tự động kết nối lại**: Thiết lập cơ chế tự động kết nối lại khi phát hiện mất kết nối
2. **Backoff tăng dần**: Tăng dần thời gian chờ giữa các lần thử kết nối lại để tránh quá tải server
3. **Lưu trữ offline**: Lưu tin nhắn đang soạn hoặc chưa gửi được vào bộ nhớ cục bộ
4. **Hiển thị trạng thái**: Cập nhật UI để hiển thị trạng thái kết nối cho người dùng

### Ví dụ backoff tăng dần

```javascript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function reconnectWithBackoff() {
  if (reconnectAttempts >= maxReconnectAttempts) {
    console.log("Đã đạt đến số lần thử kết nối tối đa");
    return;
  }

  // Tính toán thời gian chờ với backoff theo cấp số nhân
  const backoffTime = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
  console.log(`Thử kết nối lại sau ${backoffTime}ms`);

  setTimeout(() => {
    reconnectAttempts++;
    initializeChatWebSocket(roomName, token);
  }, backoffTime);
}
```

## Tối ưu hóa hiệu suất

1. **Gộp tin nhắn**: Khi hiển thị nhiều tin nhắn cùng lúc, gộp chúng thành một lần cập nhật DOM
2. **Phân trang**: Tải tin nhắn theo trang khi hiển thị lịch sử tin nhắn dài
3. **Nén dữ liệu**: Giảm kích thước dữ liệu truyền qua WebSocket khi cần
4. **Xử lý ngắt quãng**: Sử dụng requestAnimationFrame để cập nhật UI mượt mà

## Danh sách kiểm tra triển khai

- [ ] Xác thực JWT token
- [ ] Xử lý và hiển thị tin nhắn nhận được
- [ ] Xử lý lỗi và mất kết nối
- [ ] Tự động kết nối lại
- [ ] Hiển thị trạng thái kết nối
- [ ] Xử lý chỉ báo đang nhập
- [ ] Xử lý cuộn và hiển thị lịch sử tin nhắn

## Thực hành tốt nhất

1. **Bảo mật**: Không lưu JWT token trong localStorage, ưu tiên sử dụng httpOnly cookies
2. **Validation**: Kiểm tra dữ liệu trước khi gửi và sau khi nhận
3. **Debounce**: Áp dụng debounce cho các sự kiện như typing indicator
4. **Lazy loading**: Tải tin nhắn theo nhu cầu khi người dùng cuộn
5. **Error handling**: Bao gồm xử lý lỗi ở mọi bước
