# Hướng dẫn sử dụng Admin và Chat

## Các thay đổi đã thực hiện

1. **Thống nhất cách kiểm tra quyền Admin**

   - Đã sửa lại class `IsAdminUser` trong cả hai file chat/permissions.py và accounts/permissions.py để sử dụng cùng một tiêu chuẩn
   - Admin được xác định chỉ qua thuộc tính `is_admin=True`

2. **Thêm công cụ xác minh tài khoản Admin**

   - `create_admin.py`: Script để tạo tài khoản admin mới hoặc cập nhật quyền admin cho tài khoản hiện có
   - `check_admin_accounts.py`: Script để kiểm tra và đảm bảo tài khoản admin có đầy đủ các thuộc tính cần thiết

3. **Cải thiện WebSocket cho Chat**

   - Đã cập nhật `chat/routing.py` để hỗ trợ đúng định dạng username (bao gồm dấu chấm, @ và các ký tự đặc biệt)
   - Thêm log chi tiết vào ChatConsumer để dễ dàng debug

4. **Phân quyền rõ ràng hơn**

   - Đã xác nhận rằng tất cả các API admin đều đã được bảo vệ bằng permission_classes=[IsAdminUser]

5. **Cải thiện API Endpoint**
   - Thêm thông báo deprecation cho `/api/` và khuyến khích sử dụng `/api/v1/`
   - Thêm middleware để tự động đính kèm thông báo deprecation vào các response từ đường dẫn cũ

## Cách sử dụng

### 1. Tạo tài khoản Admin

```bash
python create_admin.py <username> <email> <password>
```

Ví dụ:

```bash
python create_admin.py admin admin@example.com admin123
```

### 2. Kiểm tra các tài khoản Admin

```bash
python check_admin_accounts.py
```

Script này sẽ:

- Hiển thị danh sách tất cả các tài khoản admin, staff hoặc superuser
- Cảnh báo bất kỳ tài khoản nào có phân quyền không nhất quán
- Cho phép bạn cập nhật các tài khoản không nhất quán

### 3. Sử dụng Chat

Chat bây giờ hoạt động thông qua WebSocket. Kết nối WebSocket theo định dạng:

```
ws://<domain>/ws/chat/<username_nguoi_nhan>/
```

Ví dụ:

```
ws://localhost:8000/ws/chat/user123/
```

Hãy đảm bảo truyền token JWT trong header của kết nối WebSocket để xác thực người dùng.

### 4. Các API Admin

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
