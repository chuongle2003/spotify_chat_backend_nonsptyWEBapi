# Hướng dẫn sử dụng Admin và Chat

## Các thay đổi đã thực hiện

1. **Thống nhất cách kiểm tra quyền Admin**

   - Đã sửa lại class `IsAdminUser` trong cả hai file chat/permissions.py và accounts/permissions.py để sử dụng cùng một tiêu chuẩn
   - Admin được xác định chỉ qua thuộc tính `is_admin=True`

2. **Thêm công cụ xác minh tài khoản Admin**

   - `create_admin.py`: Script để tạo tài khoản admin mới hoặc cập nhật quyền admin cho tài khoản hiện có
   - `check_admin_accounts.py`: Script để kiểm tra và đảm bảo tài khoản admin có đầy đủ các thuộc tính cần thiết
   - Thêm các command Django để quản lý tài khoản admin: `update_admin_accounts` và `create_admin_user`

3. **Cải thiện WebSocket cho Chat**

   - Đã cập nhật `chat/routing.py` để hỗ trợ đúng định dạng username (bao gồm dấu chấm, @ và các ký tự đặc biệt)
   - Thêm log chi tiết vào ChatConsumer để dễ dàng debug

4. **Phân quyền rõ ràng hơn**

   - Đã xác nhận rằng tất cả các API admin đều đã được bảo vệ bằng permission_classes=[IsAdminUser]

5. **Cải thiện API Endpoint**
   - Thêm thông báo deprecation cho `/api/` và khuyến khích sử dụng `/api/v1/`
   - Thêm middleware để tự động đính kèm thông báo deprecation vào các response từ đường dẫn cũ
   - Đã thêm AdminViewSet vào router trong accounts/urls.py

## Chi tiết cấu hình WebSocket cho Chat

### 1. Định nghĩa URL WebSocket

WebSocket được định nghĩa trong file `chat/routing.py`:

```python
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>[\w.@+-]+)/$", consumers.ChatConsumer.as_asgi()),
]
```

URL này cho phép kết nối WebSocket theo định dạng:

```
ws://<domain>/ws/chat/<username_người_nhận>/
```

Pattern `[\w.@+-]+` cho phép username chứa:

- Chữ cái và số (`\w`)
- Dấu chấm (`.`)
- Ký tự @ (`@`)
- Dấu cộng (`+`)
- Dấu trừ (`-`)

### 2. Consumer xử lý WebSocket

Consumer được định nghĩa trong `chat/consumers.py`:

#### Kết nối

```python
async def connect(self):
    self.user = self.scope["user"]          # Lấy thông tin người dùng từ JWT token
    self.room_name = self.scope['url_route']['kwargs']['room_name']  # Lấy username người nhận

    # Kiểm tra xác thực
    if not self.user.is_authenticated:
        print("Người dùng chưa đăng nhập, đóng kết nối WebSocket")
        await self.close(code=4001)
        return

    # Lấy thông tin người nhận
    self.receiver = await self.get_user_by_username(self.room_name)
    if not self.receiver:
        print(f"Không tìm thấy người dùng với username {self.room_name}")
        await self.close(code=4004)
        return

    # Tạo tên nhóm duy nhất cho cuộc trò chuyện
    user_ids = sorted([str(self.user.id), str(self.receiver.id)])
    self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

    # Thêm vào nhóm chat và chấp nhận kết nối
    await self.channel_layer.group_add(self.room_group_name, self.channel_name)
    await self.accept()
```

#### Nhận tin nhắn

```python
async def receive(self, text_data):
    data = json.loads(text_data)
    message = data['message']
    username = data['username']

    # Lưu tin nhắn vào database
    await self.save_message(username, self.room_name, message)

    # Gửi tin nhắn đến tất cả người dùng trong nhóm
    await self.channel_layer.group_send(
        self.room_group_name,
        {
            'type': 'chat_message',
            'message': message,
            'username': username,
        }
    )
```

### 3. Xác thực WebSocket

Xác thực dựa trên JWT token được truyền trong header kết nối WebSocket. Token được xử lý thông qua ASGI middleware để xác thực người dùng.

### 4. Lưu trữ tin nhắn

Khi nhận được tin nhắn mới, hệ thống:

1. Lưu tin nhắn vào database trong bảng `Message`
2. Gửi tin nhắn tới tất cả người dùng đang kết nối trong cùng room

### 5. Nhóm Chat

Mỗi cuộc trò chuyện 1-1 được định danh bằng `room_group_name` có dạng:

```
chat_<user_id1>_<user_id2>
```

User ID được sắp xếp để đảm bảo cùng một cuộc trò chuyện luôn có cùng tên nhóm, bất kể ai kết nối trước.

### 6. Ví dụ sử dụng (JavaScript)

#### Kết nối

```javascript
const websocket = new WebSocket(`ws://example.com/ws/chat/username2/`);
// Thêm token JWT vào header
websocket.setRequestHeader("Authorization", "Bearer <jwt_token>");
```

#### Gửi tin nhắn

```javascript
websocket.send(
  JSON.stringify({
    message: "Xin chào!",
    username: "username1",
  })
);
```

#### Nhận tin nhắn

```javascript
websocket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  console.log(`${data.username}: ${data.message}`);
};
```

## Cách sử dụng

### 1. Tạo tài khoản Admin

Sử dụng script có sẵn:

```bash
python create_admin.py <username> <email> <password>
```

Hoặc sử dụng Django management command:

```bash
python manage.py create_admin_user <username> <email> <password>
```

Ví dụ:

```bash
python manage.py create_admin_user admin admin@example.com admin123
```

### 2. Kiểm tra và cập nhật các tài khoản Admin

Sử dụng script có sẵn:

```bash
python check_admin_accounts.py
```

Hoặc sử dụng Django management command:

```bash
# Chỉ kiểm tra
python manage.py update_admin_accounts

# Tự động sửa
python manage.py update_admin_accounts --fix

# Cập nhật một tài khoản cụ thể
python manage.py update_admin_accounts --username=admin --fix
```

### 3. Truy cập API Admin để quản lý người dùng

API quản lý người dùng:

```
/api/v1/accounts/admin/users/
```

Các endpoint chi tiết:

- Danh sách người dùng: GET `/api/v1/accounts/admin/users/`
- Chi tiết người dùng: GET `/api/v1/accounts/admin/users/{id}/`
- Tạo người dùng mới: POST `/api/v1/accounts/admin/users/`
- Cập nhật người dùng: PUT/PATCH `/api/v1/accounts/admin/users/{id}/`
- Xóa người dùng: DELETE `/api/v1/accounts/admin/users/{id}/`
- Xem thông tin đầy đủ: GET `/api/v1/accounts/admin/users/{id}/complete/`
- Bật/tắt tài khoản: POST `/api/v1/accounts/admin/users/{id}/toggle_active/`
- Cấp/thu hồi quyền admin: POST `/api/v1/accounts/admin/users/{id}/toggle_admin/`

### 4. Sử dụng Chat

Chat bây giờ hoạt động thông qua WebSocket. Kết nối WebSocket theo định dạng:

```
ws://<domain>/ws/chat/<username_nguoi_nhan>/
```

Ví dụ:

```
ws://localhost:8000/ws/chat/user123/
```

Hãy đảm bảo truyền token JWT trong header của kết nối WebSocket để xác thực người dùng.

### 5. Các API Admin cho Chat

Tất cả các API admin có thể được truy cập tại:

```
/api/v1/chat/admin/...
```

Ví dụ:

- Quản lý tin nhắn: `/api/v1/chat/admin/messages/`
- Quản lý báo cáo: `/api/v1/chat/admin/reports/`
- Thống kê báo cáo: `/api/v1/chat/admin/reports/statistics/`
- Báo cáo đang chờ xử lý: `/api/v1/chat/admin/reports/pending/`
- Quản lý hạn chế chat: `/api/v1/chat/admin/restrictions/`
- Thống kê chat của người dùng: `/api/v1/chat/admin/stats/`

Tất cả các API admin đều yêu cầu xác thực JWT và người dùng phải có quyền admin (is_admin=True).

## Lưu ý

1. **API Deprecated**: Các API bắt đầu bằng `/api/` (không phải `/api/v1/`) vẫn hoạt động để tương thích ngược, nhưng sẽ có thông báo deprecated. Hãy sử dụng `/api/v1/` cho tất cả các request mới.

2. **Admin Access**: Người dùng được coi là admin nếu họ có thuộc tính `is_admin=True`. Tất cả các superuser tự động có `is_admin=True`.

3. **WebSocket Auth**: Đảm bảo truyền token JWT đúng cách trong header của kết nối WebSocket.

## Khắc phục sự cố Admin

Nếu bạn không thể truy cập các tính năng admin hoặc không thể tải danh sách người dùng, hãy thử các bước sau:

1. **Kiểm tra tài khoản admin**:

   ```bash
   python manage.py update_admin_accounts
   ```

2. **Sửa chữa tài khoản admin**:

   ```bash
   python manage.py update_admin_accounts --fix
   ```

3. **Tạo mới tài khoản admin nếu cần**:

   ```bash
   python manage.py create_admin_user new_admin admin@example.com password123
   ```

4. **Xác nhận API endpoints**:

   - Đảm bảo bạn đang sử dụng đúng URL: `/api/v1/accounts/admin/users/`
   - Đảm bảo bạn đã đăng nhập bằng tài khoản có `is_admin=True`

5. **Kiểm tra logs**:
   - Kiểm tra logs Django để xem lỗi chi tiết
