# AI Assistant cho Spotify Chat

## Giới thiệu

AI Assistant là một module tích hợp vào Spotify Chat Backend, sử dụng Gemini API của Google để cung cấp trải nghiệm chat thông minh. Module này cho phép người dùng tương tác với chatbot AI để nhận thông tin hỗ trợ về ứng dụng, âm nhạc, và các tính năng khác.

## Tính năng

- Chat với trợ lý AI theo nhiều ngữ cảnh khác nhau (chung, âm nhạc, chat, playlist, kỹ thuật)
- Lưu trữ lịch sử hội thoại để tham khảo sau
- Hỗ trợ xử lý văn bản và hình ảnh (multimodal)
- Tương tác real-time qua WebSocket
- Cá nhân hóa ngữ cảnh hệ thống
- Quản lý hội thoại qua REST API

## Cài đặt

1. **Thêm dependency**: Thêm `google-generativeai` vào file `requirements.txt`:

   ```
   google-generativeai==0.8.5
   ```

2. **Thiết lập API key**: Thêm API key Gemini vào file `.env` của dự án:

   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Thêm ứng dụng vào INSTALLED_APPS**: Cập nhật file `settings.py`:

   ```python
   INSTALLED_APPS = [
       # ... other apps
       'ai_assistant.apps.AIAssistantConfig',
   ]
   ```

4. **Cập nhật URLs**: Thêm đường dẫn vào file `urls.py` chính:

   ```python
   urlpatterns = [
       # ... other url patterns
       path('api/v1/ai/', include('ai_assistant.urls')),
   ]
   ```

5. **Cập nhật định tuyến WebSocket**: Cập nhật file `asgi.py` để bao gồm WebSocket pattern của AI Assistant:

   ```python
   from channels.routing import ProtocolTypeRouter, URLRouter
   from channels.auth import AuthMiddlewareStack
   from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
   from ai_assistant.routing import websocket_urlpatterns as ai_websocket_urlpatterns

   # Combine patterns
   all_websocket_urlpatterns = chat_websocket_urlpatterns + ai_websocket_urlpatterns

   application = ProtocolTypeRouter({
       "http": django_asgi_app,
       "websocket": AuthMiddlewareStack(
           URLRouter(
               all_websocket_urlpatterns
           )
       ),
   })
   ```

6. **Chạy migrations**: Tạo và áp dụng các migrations cho ứng dụng:
   ```
   python manage.py makemigrations ai_assistant
   python manage.py migrate
   ```

## Sử dụng

### API Endpoints

- `GET /api/v1/ai/chat/` - Giao diện web để tương tác với AI
- `GET /api/v1/ai/guide/` - Trang hướng dẫn sử dụng AI Assistant
- `POST /api/v1/ai/generate-text/` - API để gửi câu hỏi văn bản
- `POST /api/v1/ai/generate-multimodal/` - API để gửi câu hỏi kèm hình ảnh
- `GET /api/v1/ai/system-instructions/` - Lấy danh sách các ngữ cảnh hệ thống có sẵn

### WebSocket

- `ws://example.com/ws/ai/chat/` - Kết nối WebSocket cho hội thoại mới
- `ws://example.com/ws/ai/chat/<conversation_id>/` - Kết nối WebSocket để tiếp tục hội thoại

### Tin nhắn WebSocket

Để gửi tin nhắn qua WebSocket:

```javascript
socket.send(
  JSON.stringify({
    type: "message",
    message: "Câu hỏi của người dùng",
    conversation_id: null, // hoặc ID hội thoại nếu tiếp tục hội thoại cũ
    system_context: "Ngữ cảnh hệ thống (tùy chọn)",
  })
);
```

## Tùy chỉnh ngữ cảnh hệ thống

Ngữ cảnh hệ thống giúp định hướng AI về vai trò và cách trả lời. Các ngữ cảnh mặc định:

- **General**: Hỗ trợ chung về Spotify Chat
- **Music**: Tập trung vào thông tin âm nhạc, nghệ sĩ, và thể loại
- **Chat**: Hỗ trợ hiểu các tính năng chat
- **Playlists**: Hỗ trợ quản lý và khám phá playlist
- **Technical**: Thông tin kỹ thuật dành cho nhà phát triển

## Phát triển

### Mô hình dữ liệu

- `AIConversation`: Lưu trữ thông tin về hội thoại
- `AIMessage`: Lưu trữ các tin nhắn trong hội thoại
- `AISystemPrompt`: Lưu trữ các ngữ cảnh hệ thống có sẵn

### Cấu trúc

- `models.py` - Định nghĩa mô hình dữ liệu
- `views.py` - API endpoints và views
- `serializers.py` - Serializers cho REST API
- `gemini_client.py` - Client tương tác với Gemini API
- `consumers.py` - WebSocket consumers
- `routing.py` - WebSocket URL routing
- `urls.py` - URL routing cho REST API

## Vấn đề thường gặp

1. **Lỗi kết nối WebSocket**: Đảm bảo cấu hình ASGI và Channels đúng
2. **API key không hoạt động**: Kiểm tra lại API key và quyền truy cập
3. **Lỗi serialize/deserialize**: Kiểm tra định dạng dữ liệu gửi qua API

## Giấy phép

Giống như phần còn lại của dự án Spotify Chat Backend.
