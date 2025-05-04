# Hướng dẫn sử dụng AI Assistant

## Tổng quan

AI Assistant là một module tích hợp vào Spotify Chat cho phép người dùng tương tác với trợ lý AI thông minh được hỗ trợ bởi Google Gemini. Module này cung cấp khả năng hỗ trợ người dùng qua chat, trả lời câu hỏi, đề xuất nội dung âm nhạc và xử lý hình ảnh (multimodal).

## Chức năng chính

### 1. Chat Thông Minh

- **Trả lời câu hỏi**: Nhận câu trả lời thông minh cho các câu hỏi về âm nhạc, nghệ sĩ, sử dụng ứng dụng, v.v.
- **Lưu trữ lịch sử**: Duy trì ngữ cảnh trong cuộc trò chuyện để cung cấp trả lời nhất quán
- **Ngữ cảnh tùy chỉnh**: Đặt hướng dẫn hệ thống khác nhau để tùy chỉnh cách AI trả lời

### 2. Xử lý đa phương tiện (Multimodal)

- **Phân tích hình ảnh**: Gửi hình ảnh kèm theo văn bản để AI phân tích
- **Nhận diện nhạc/nghệ sĩ**: Tải lên hình ảnh album, nhạc cụ, hoặc nghệ sĩ để nhận thông tin
- **Xử lý ảnh chụp màn hình**: Phân tích ảnh chụp màn hình của ứng dụng để hỗ trợ giải quyết vấn đề

### 3. Quản lý cuộc trò chuyện

- **Tạo cuộc trò chuyện mới**: Bắt đầu hội thoại với chủ đề cụ thể
- **Xem lịch sử**: Truy cập và tiếp tục các cuộc trò chuyện trước đó
- **Xóa tin nhắn**: Xóa lịch sử tin nhắn trong khi giữ nguyên cuộc trò chuyện

### 4. Hỗ trợ theo ngữ cảnh

- **Trợ lý âm nhạc**: Hỗ trợ khám phá nhạc, tìm hiểu về nghệ sĩ và thể loại
- **Hỗ trợ kỹ thuật**: Giải đáp câu hỏi về cách sử dụng ứng dụng và xử lý sự cố
- **Phát triển playlist**: Đề xuất bài hát và cách xây dựng playlist hiệu quả

## REST API Endpoints

### Quản lý cuộc trò chuyện

| Phương thức | Endpoint                                  | Mô tả                                     |
| ----------- | ----------------------------------------- | ----------------------------------------- |
| GET         | `/api/v1/ai/conversations/`               | Lấy danh sách hội thoại AI của người dùng |
| POST        | `/api/v1/ai/conversations/`               | Tạo hội thoại AI mới                      |
| GET         | `/api/v1/ai/conversations/{id}/`          | Xem chi tiết hội thoại AI                 |
| DELETE      | `/api/v1/ai/conversations/{id}/`          | Xóa hội thoại AI                          |
| GET         | `/api/v1/ai/conversations/{id}/messages/` | Lấy tin nhắn trong hội thoại              |
| DELETE      | `/api/v1/ai/conversations/{id}/clear/`    | Xóa tất cả tin nhắn trong hội thoại       |

### Tương tác với AI

| Phương thức | Endpoint                          | Mô tả                                   |
| ----------- | --------------------------------- | --------------------------------------- |
| POST        | `/api/v1/ai/generate-text/`       | Tạo phản hồi văn bản từ AI              |
| POST        | `/api/v1/ai/generate-multimodal/` | Tạo phản hồi từ văn bản + hình ảnh      |
| GET         | `/api/v1/ai/system-instructions/` | Lấy danh sách hướng dẫn hệ thống có sẵn |
| GET         | `/api/v1/ai/system-prompts/`      | Lấy danh sách prompt hệ thống           |

### HTML và giao diện trực quan

| Phương thức | Endpoint            | Mô tả                          |
| ----------- | ------------------- | ------------------------------ |
| GET         | `/api/v1/ai/chat/`  | Giao diện chat AI trực quan    |
| GET         | `/api/v1/ai/guide/` | Hướng dẫn sử dụng AI Assistant |

## Cấu trúc dữ liệu

### Cuộc trò chuyện (AIConversation)

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

### Tin nhắn AI (AIMessage)

```json
{
  "id": 1,
  "role": "user",
  "content": "Làm thế nào để tạo playlist?",
  "created_at": "2023-11-20T14:30:00Z",
  "has_image": false
}
```

### System Prompt

```json
{
  "id": 1,
  "name": "Trợ lý âm nhạc",
  "description": "Prompt hệ thống cho trợ lý âm nhạc",
  "prompt_text": "Bạn là một trợ lý âm nhạc thông thạo các thể loại nhạc, nghệ sĩ và lịch sử âm nhạc...",
  "created_at": "2023-10-15T09:00:00Z",
  "updated_at": "2023-10-15T09:00:00Z"
}
```

## API Requests

### 1. Tạo cuộc trò chuyện mới

```
POST /api/v1/ai/conversations/
Content-Type: application/json
Authorization: Bearer {your_token}

{
  "title": "Hỏi về cách sử dụng playlist",
  "system_context": "Bạn là trợ lý âm nhạc, giúp người dùng tìm hiểu về các tính năng của ứng dụng"
}
```

**Phản hồi thành công (200 OK):**

```json
{
  "id": 1,
  "title": "Hỏi về cách sử dụng playlist",
  "user": {
    "id": 123,
    "username": "user123"
  },
  "system_context": "Bạn là trợ lý âm nhạc, giúp người dùng tìm hiểu về các tính năng của ứng dụng",
  "created_at": "2023-11-20T14:30:00Z",
  "updated_at": "2023-11-20T14:30:00Z",
  "messages": []
}
```

### 2. Gửi tin nhắn văn bản

```
POST /api/v1/ai/generate-text/
Content-Type: application/json
Authorization: Bearer {your_token}

{
  "prompt": "Làm thế nào để tạo playlist?",
  "conversation_id": 1,
  "system_context": "Bạn là trợ lý âm nhạc"
}
```

**Phản hồi thành công (200 OK):**

```json
{
  "response": "Để tạo playlist, bạn có thể nhấn vào nút 'Tạo playlist mới' ở góc trên bên phải của trang chủ...",
  "conversation_id": 1
}
```

### 3. Gửi tin nhắn có hình ảnh

```
POST /api/v1/ai/generate-multimodal/
Content-Type: multipart/form-data
Authorization: Bearer {your_token}

prompt: "Bạn có thể nói cho tôi đây là bài hát gì không?"
image: [file_data]
conversation_id: 1
system_context: "Bạn là trợ lý nhận diện âm nhạc"
```

**Phản hồi thành công (200 OK):**

```json
{
  "response": "Dựa vào hình ảnh album cover, đây là bài hát 'Shape of You' của Ed Sheeran, phát hành năm 2017 trong album '÷ (Divide)'...",
  "conversation_id": 1
}
```

### 4. Lấy danh sách cuộc trò chuyện

```
GET /api/v1/ai/conversations/
Authorization: Bearer {your_token}
```

**Phản hồi thành công (200 OK):**

```json
[
  {
    "id": 1,
    "title": "Hỏi về cách sử dụng playlist",
    "user": {
      "id": 123,
      "username": "user123"
    },
    "created_at": "2023-11-20T14:30:00Z",
    "updated_at": "2023-11-20T16:45:00Z"
  },
  {
    "id": 2,
    "title": "Tìm hiểu về nghệ sĩ",
    "user": {
      "id": 123,
      "username": "user123"
    },
    "created_at": "2023-11-21T10:15:00Z",
    "updated_at": "2023-11-21T10:45:00Z"
  }
]
```

### 5. Xóa tin nhắn trong cuộc trò chuyện

```
DELETE /api/v1/ai/conversations/1/clear/
Authorization: Bearer {your_token}
```

**Phản hồi thành công (204 No Content)**

### 6. Lấy danh sách hướng dẫn hệ thống có sẵn

```
GET /api/v1/ai/system-instructions/
Authorization: Bearer {your_token}
```

**Phản hồi thành công (200 OK):**

```json
{
  "general": "You are a helpful AI assistant that can answer questions about the Spotify Chat system. Answer concisely and accurately.",
  "music": "You are a music assistant that can help users discover new music, understand genres, and learn about artists. Focus on providing music-related information.",
  "chat": "You are a chat assistant that can help users understand how to use the chat features of the Spotify Chat app.",
  "playlists": "You are a playlist assistant that helps users manage and discover music playlists.",
  "technical": "You are a technical assistant that can help developers understand the API and backend details of the Spotify Chat app."
}
```

## WebSocket API

### 1. Kết nối WebSocket cho cuộc trò chuyện AI

```javascript
// Kết nối đến cuộc hội thoại AI (với ID cuộc trò chuyện đã có)
const socket = new WebSocket(
  `wss://spotifybackend.shop/ws/ai/chat/${conversationId}/`
);

// Hoặc tạo cuộc trò chuyện mới
const socket = new WebSocket(`wss://spotifybackend.shop/ws/ai/chat/`);

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

### 2. Định dạng tin nhắn WebSocket

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
  "conversation_id": 1,
  "user_id": 123
}
```

#### Thông báo đang nhập

```json
{
  "type": "typing",
  "is_typing": true,
  "role": "assistant",
  "user_id": 123
}
```

## Quy trình sử dụng

### Quy trình 1: Chat đơn giản với AI

1. **Tạo cuộc trò chuyện mới** (nếu chưa có):

   ```
   POST /api/v1/ai/conversations/
   ```

2. **Gửi câu hỏi đến AI**:

   ```
   POST /api/v1/ai/generate-text/
   ```

3. **Xem lịch sử trò chuyện**:
   ```
   GET /api/v1/ai/conversations/{id}/messages/
   ```

### Quy trình 2: Chat với hình ảnh (Multimodal)

1. **Chuẩn bị hình ảnh** (định dạng JPG, PNG, GIF)

2. **Gửi hình ảnh kèm câu hỏi**:

   ```
   POST /api/v1/ai/generate-multimodal/
   ```

3. **Xử lý phản hồi** (bao gồm thông tin về hình ảnh)

### Quy trình 3: Sử dụng WebSocket cho chat real-time

1. **Thiết lập kết nối WebSocket**:

   ```javascript
   const socket = new WebSocket(
     `wss://spotifybackend.shop/ws/ai/chat/${conversationId}/`
   );
   ```

2. **Xử lý tin nhắn đến**:

   ```javascript
   socket.onmessage = (event) => {
     const data = JSON.parse(event.data);
     // Xử lý tin nhắn
   };
   ```

3. **Gửi tin nhắn**:
   ```javascript
   socket.send(
     JSON.stringify({
       type: "message",
       message: "Câu hỏi của bạn",
     })
   );
   ```

## Lưu ý phát triển

1. **Xác thực**: Tất cả API đều yêu cầu xác thực JWT. Đảm bảo gửi token trong header `Authorization: Bearer {token}`.

2. **Rate Limiting**: API có giới hạn tần suất gọi dựa trên hạn mức của Gemini API. Xử lý lỗi 429 (Too Many Requests) một cách phù hợp.

3. **Xử lý lỗi**: Triển khai xử lý lỗi phía client cho các tình huống:

   - Kết nối bị mất
   - Lỗi xác thực
   - Lỗi server

4. **Kích thước hình ảnh**: Đối với API multimodal, kích thước hình ảnh tối đa là 20MB và nên được tối ưu hóa trước khi gửi.

5. **WebSocket Timeout**: Kết nối WebSocket có thể bị đóng sau một khoảng thời gian không hoạt động. Triển khai cơ chế kết nối lại tự động.

## Xử lý lỗi

| Mã lỗi | Mô tả                                   | Xử lý                                                |
| ------ | --------------------------------------- | ---------------------------------------------------- |
| 400    | Bad Request - Dữ liệu không hợp lệ      | Kiểm tra format và tham số của request               |
| 401    | Unauthorized - Chưa xác thực            | Đảm bảo token JWT hợp lệ và chưa hết hạn             |
| 403    | Forbidden - Không có quyền              | Kiểm tra quyền của người dùng                        |
| 404    | Not Found - Không tìm thấy tài nguyên   | Kiểm tra ID cuộc trò chuyện và endpoint              |
| 429    | Too Many Requests - Vượt quá rate limit | Thực hiện retry sau một khoảng thời gian             |
| 500    | Internal Server Error                   | Liên hệ đội phát triển với thông tin chi tiết về lỗi |

## Ví dụ code tích hợp (JavaScript)

```javascript
// Lớp API cho AI Assistant
class AIAssistant {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
    this.socket = null;
    this.conversationId = null;
  }

  // Tạo cuộc trò chuyện mới
  async createConversation(title, systemContext) {
    const response = await fetch(`${this.baseUrl}/api/v1/ai/conversations/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
      },
      body: JSON.stringify({ title, system_context: systemContext }),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    const data = await response.json();
    this.conversationId = data.id;
    return data;
  }

  // Gửi tin nhắn văn bản
  async sendTextMessage(prompt, conversationId, systemContext) {
    const response = await fetch(`${this.baseUrl}/api/v1/ai/generate-text/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
      },
      body: JSON.stringify({
        prompt,
        conversation_id: conversationId || this.conversationId,
        system_context: systemContext,
      }),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    return await response.json();
  }

  // Kết nối WebSocket
  connectWebSocket(conversationId, onMessage, onTyping) {
    const wsProtocol =
      window.location.protocol === "https:" ? "wss://" : "ws://";
    const wsUrl = conversationId
      ? `${wsProtocol}${this.baseUrl.replace(
          /^https?:\/\//,
          ""
        )}/ws/ai/chat/${conversationId}/`
      : `${wsProtocol}${this.baseUrl.replace(/^https?:\/\//, "")}/ws/ai/chat/`;

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log("WebSocket connected");
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "message") {
        if (onMessage) onMessage(data.message, data);
        if (data.conversation_id && !this.conversationId) {
          this.conversationId = data.conversation_id;
        }
      } else if (data.type === "typing") {
        if (onTyping) onTyping(data.is_typing);
      }
    };

    this.socket.onclose = () => {
      console.log("WebSocket disconnected");
      // Implement reconnection logic if needed
    };

    return this.socket;
  }

  // Gửi tin nhắn qua WebSocket
  sendMessageViaWebSocket(message, systemContext) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket not connected");
    }

    this.socket.send(
      JSON.stringify({
        type: "message",
        message,
        conversation_id: this.conversationId,
        system_context: systemContext,
      })
    );
  }
}

// Sử dụng
const aiAssistant = new AIAssistant(
  "https://spotifybackend.shop",
  "your_token_here"
);

// Tạo cuộc trò chuyện
aiAssistant
  .createConversation("Hỏi về playlist", "Bạn là trợ lý âm nhạc")
  .then((conversation) => {
    console.log("Conversation created:", conversation);

    // Kết nối WebSocket
    aiAssistant.connectWebSocket(
      conversation.id,
      (message) => console.log("AI response:", message),
      (isTyping) => console.log("AI is typing:", isTyping)
    );

    // Gửi tin nhắn qua WebSocket
    aiAssistant.sendMessageViaWebSocket("Làm thế nào để tạo playlist?");
  })
  .catch((error) => console.error("Error:", error));
```
