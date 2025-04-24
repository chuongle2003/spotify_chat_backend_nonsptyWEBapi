# Hướng Dẫn Sử Dụng API Với Postman

Tài liệu này cung cấp hướng dẫn chi tiết về cách sử dụng Postman để tương tác với cấu trúc API mới của hệ thống.

## 1. Cấu Trúc API Mới

Hệ thống API của chúng tôi đã được cải tiến để đạt được tính nhất quán, dễ hiểu và tuân thủ các tiêu chuẩn RESTful tốt nhất. Dưới đây là cấu trúc API mới:

### 1.1 Cấu Trúc URL Tổng Thể

```
/api/v1/
├── auth/                  # Xác thực và phân quyền
│   ├── token/             # Lấy JWT token
│   ├── token/refresh/     # Làm mới token
│   └── logout/            # Đăng xuất
│
├── accounts/              # Quản lý tài khoản
│   ├── auth/
│   │   └── register/      # Đăng ký
│   ├── users/             # CRUD người dùng thông thường
│   │   └── me/            # Thông tin người dùng hiện tại
│   ├── public/            # Endpoints công khai
│   │   └── users/         # Danh sách người dùng công khai
│   ├── admin/             # Quản lý Admin
│   │   └── users/         # Quản lý người dùng (admin)
│   └── management/        # Quản lý cho Staff
│       └── users/         # Quản lý người dùng (staff)
│
├── music/                 # Quản lý âm nhạc
│   ├── songs/             # CRUD bài hát
│   └── playlists/         # CRUD playlist
│
└── chat/                  # Quản lý chat
    ├── messages/          # CRUD tin nhắn
    └── conversations/     # Quản lý cuộc trò chuyện
```

### 1.2 Các Điểm Khác Biệt Chính So Với Cấu Trúc Cũ

1. **API Versioning**: Đã thêm namespace `/api/v1/` để hỗ trợ nâng cấp trong tương lai
2. **Tập Trung Xác Thực**: Các endpoints xác thực được tập trung trong `/api/v1/auth/`
3. **Cấu Trúc Phân Cấp**: URLs được tổ chức theo cấu trúc phân cấp rõ ràng
4. **Nhất Quán Trong Đặt Tên**: Sử dụng quy ước đặt tên nhất quán (danh từ số nhiều, kebab-case cho URLs)
5. **Tương Thích Ngược**: Các endpoints cũ vẫn được hỗ trợ trong thời gian chuyển tiếp

## 2. Tải Xuống Và Import Collection Vào Postman

### 2.1 Tải Xuống Collection

**Phương pháp 1: Sử dụng file có sẵn**

1. Sử dụng file `POSTMAN_COLLECTION.json` và `POSTMAN_ENV.json` có sẵn trong thư mục gốc của dự án

**Phương pháp 2: Tạo từ mã nguồn**

1. Nếu bạn không thể tìm thấy các file JSON ở trên, bạn có thể tự tạo chúng bằng cách sao chép nội dung từ mã nguồn trong dự án

### 2.2 Import Collection Vào Postman

1. **Mở Postman**
2. **Click vào "Import" ở góc trên bên trái**
3. **Kéo file JSON đã tải về vào cửa sổ import, hoặc nhấp vào "Upload Files" và chọn file**
   - Đối với collection: tải lên file `POSTMAN_COLLECTION.json`
   - Đối với environment: tải lên file `POSTMAN_ENV.json`
4. **Xác nhận import bằng cách nhấp vào "Import"**

### 2.3 Thiết Lập Biến Môi Trường

1. **Tạo Môi Trường Mới**:

   - Click vào biểu tượng bánh răng (⚙️) ở góc trên bên phải
   - Chọn "Environments"
   - Click "Add" để tạo môi trường mới (bỏ qua bước này nếu bạn đã import file `POSTMAN_ENV.json`)
   - Đặt tên môi trường (vd: "Spotify Chat Dev")

2. **Thêm Các Biến Cần Thiết**:

   - `base_url`: URL cơ sở của API (vd: `http://localhost:8000`)
   - `token`: Để lưu token xác thực (ban đầu để trống)
   - `refresh_token`: Để lưu refresh token (ban đầu để trống)
   - `user_id`: ID người dùng cho các requests (ban đầu để trống)

3. **Lưu Môi Trường**:
   - Click "Save"
   - Chọn môi trường này từ dropdown ở góc trên bên phải

## 3. Sử Dụng Collection Trong Postman

### 3.1 Xác Thực

1. **Lấy Token**:

   - Mở thư mục "Authentication" trong collection
   - Chọn request "Login - Get Token"
   - Nhập email và password trong phần "Body"
   - Gửi request
   - Token sẽ tự động được lưu vào biến môi trường `token` và `refresh_token`

2. **Làm Mới Token**:

   - Mở request "Refresh Token"
   - Gửi request với refresh token hiện tại
   - Token mới sẽ tự động được lưu vào biến môi trường

3. **Đăng Xuất**:
   - Mở request "Logout"
   - Gửi request để vô hiệu hóa token hiện tại

### 3.2 Quản Lý Người Dùng

1. **Đăng Ký Người Dùng**:

   - Mở thư mục "User Management" > "Registration"
   - Nhập thông tin người dùng mới trong phần "Body"
   - Gửi request để tạo tài khoản mới

2. **Xem Thông Tin Người Dùng Hiện Tại**:

   - Mở request "Get Current User"
   - Gửi request với token đã lưu
   - Xem thông tin chi tiết về tài khoản của bạn

3. **Quản Lý Người Dùng (Admin)**:
   - Mở thư mục "Admin" trong collection
   - Chọn các request để quản lý người dùng, cấp quyền, v.v.
   - Các requests này yêu cầu quyền admin

### 3.3 Các Tests Tự Động

Collection đã bao gồm các tests tự động để xác minh API hoạt động đúng. Mỗi request đều có script tests để:

1. Kiểm tra status code
2. Xác minh định dạng phản hồi
3. Lưu dữ liệu cần thiết vào biến môi trường
4. Kiểm tra tính nhất quán của dữ liệu

### 3.4 Chạy Collection Với Runner

1. **Mở Collection Runner**:

   - Click vào "Runner" ở thanh công cụ Postman
   - Chọn collection "Spotify Chat API"

2. **Cấu Hình Runner**:

   - Chọn thư mục cần chạy (hoặc toàn bộ collection)
   - Chọn môi trường đã thiết lập
   - Thiết lập số lần lặp (thường là 1)
   - Tùy chọn "Delay" giữa các requests (vd: 500ms)

3. **Chạy Tests**:
   - Click "Start Run"
   - Xem kết quả tests để đảm bảo mọi thứ hoạt động đúng

## 4. Ví Dụ Luồng Công Việc Phổ Biến

### 4.1 Tạo Và Quản Lý Tài Khoản Admin

1. Chạy request "Login - Get Token" với thông tin admin
2. Sử dụng request "List All Users" để xem danh sách người dùng
3. Chọn một người dùng để cấp quyền bằng request "Toggle Staff Status"
4. Thiết lập quyền cụ thể với request "Set User Permissions"

### 4.2 Quản Lý Nội Dung (Content Manager)

1. Đăng nhập với tài khoản có quyền Content Manager
2. Tải lên bài hát mới với request "Upload Song"
3. Chỉnh sửa thông tin bài hát với request "Update Song"
4. Duyệt bình luận với request "Moderate Comments"

### 4.3 Trải Nghiệm Người Dùng Thông Thường

1. Đăng ký tài khoản mới với request "Register User"
2. Đăng nhập và lấy token
3. Tạo playlist mới với request "Create Playlist"
4. Tìm kiếm và thêm bài hát vào playlist với request "Add Song to Playlist"
5. Gửi tin nhắn cho người dùng khác với request "Send Message"

## 5. Xử Lý Lỗi Phổ Biến

### 5.1 Lỗi Xác Thực

- **401 Unauthorized**: Token không hợp lệ hoặc đã hết hạn. Thử làm mới token.
- **403 Forbidden**: Tài khoản không có đủ quyền. Kiểm tra phân quyền.

### 5.2 Lỗi Dữ Liệu

- **400 Bad Request**: Dữ liệu gửi đi không hợp lệ. Kiểm tra định dạng JSON.
- **422 Validation Error**: Dữ liệu không đáp ứng yêu cầu validation. Đọc thông báo lỗi.

### 5.3 Lỗi Hệ Thống

- **500 Internal Server Error**: Lỗi server. Liên hệ team phát triển.
- **504 Gateway Timeout**: Server quá tải hoặc không phản hồi. Thử lại sau.

## 6. Tài Nguyên Hỗ Trợ

- [Tài Liệu API Đầy Đủ](docs/API_SPECIFICATION_UPDATED.md)
- [Kế Hoạch Triển Khai](docs/IMPLEMENTATION_PLAN.md)
- [Repository GitHub](https://github.com/your-repo)
- [Kênh Hỗ Trợ](mailto:support@yourcompany.com)

---

Nếu bạn có bất kỳ câu hỏi hoặc gặp vấn đề khi sử dụng API, vui lòng liên hệ với chúng tôi qua email support@yourcompany.com hoặc tạo issue trên GitHub repository.
