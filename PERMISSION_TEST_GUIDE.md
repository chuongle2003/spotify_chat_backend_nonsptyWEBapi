# Hướng dẫn Test Tạo Tài khoản Admin và Phân Quyền

## Mục lục

1. [Tạo tài khoản Admin](#1-tạo-tài-khoản-admin)
2. [Tạo Regular User và cấp quyền Staff](#2-tạo-regular-user-và-cấp-quyền-staff)
3. [Cấp quyền quản lý cụ thể cho Staff](#3-cấp-quyền-quản-lý-cụ-thể-cho-staff)
4. [Test các chức năng của từng loại người dùng](#4-test-các-chức-năng-của-từng-loại-người-dùng)
5. [Test các hạn chế quyền](#5-test-các-hạn-chế-quyền)
6. [Quy trình phân quyền đầy đủ](#6-quy-trình-phân-quyền-đầy-đủ)
7. [Chức năng chi tiết của mỗi loại người dùng](#7-chức-năng-chi-tiết-của-mỗi-loại-người-dùng)
8. [Postman Collection Full Flow](#8-postman-collection-full-flow)

## 1. Tạo tài khoản Admin

### 1.1. Tạo Admin qua Command Line (cách đảm bảo nhất)

```bash
# Mở terminal và kích hoạt môi trường ảo (nếu có)
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Tạo superuser
python manage.py createsuperuser

# Theo hướng dẫn nhập thông tin:
# Email: admin@example.com
# Username: admin
# Password: StrongAdminPassword123
# Password (confirm): StrongAdminPassword123
```

### 1.2. Lấy token của Admin để sử dụng trong các API

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/auth/token/`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body:
  ```json
  {
    "email": "admin@example.com",
    "password": "StrongAdminPassword123"
  }
  ```

**Response**:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Test Script**:

```javascript
pm.test("Admin login successful", function () {
  pm.response.to.have.status(200);
  var jsonData = pm.response.json();
  pm.environment.set("admin_token", jsonData.access);
  console.log("Admin token set");
});
```

## 2. Tạo Regular User và cấp quyền Staff

### 2.1. Đăng ký Regular User

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/accounts/auth/register/`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body:
  ```json
  {
    "username": "staffuser",
    "email": "staff@example.com",
    "password": "StrongPassword123",
    "first_name": "Staff",
    "last_name": "User"
  }
  ```

**Response**:

```json
{
  "id": 2,
  "username": "staffuser",
  "email": "staff@example.com",
  "first_name": "Staff",
  "last_name": "User",
  "avatar": null,
  "bio": ""
}
```

**Test Script**:

```javascript
pm.test("User registration successful", function () {
  pm.response.to.have.status(201);
  var jsonData = pm.response.json();
  pm.environment.set("staff_id", jsonData.id);
  console.log("Staff ID set: " + jsonData.id);
});
```

### 2.2. Cấp quyền Staff (Admin only)

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/user-management/{{staff_id}}/toggle_staff/`
- Headers:
  ```
  Authorization: Bearer {{admin_token}}
  ```

**Response**:

```json
{
  "status": "User made staff"
}
```

**Test Script**:

```javascript
pm.test("Make user staff successful", function () {
  pm.response.to.have.status(200);
  pm.expect(pm.response.json().status).to.include("staff");
});
```

## 3. Cấp quyền quản lý cụ thể cho Staff

### 3.1. Cấp quyền User Manager

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/user-management/{{staff_id}}/set_permissions/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{admin_token}}
  ```
- Body:
  ```json
  {
    "can_manage_users": true,
    "can_manage_content": false,
    "can_manage_playlists": false
  }
  ```

**Response**:

```json
{
  "status": "Permissions updated"
}
```

**Test Script**:

```javascript
pm.test("Set User Manager permission successful", function () {
  pm.response.to.have.status(200);
  pm.expect(pm.response.json().status).to.eql("Permissions updated");
  console.log("User Manager permission set");
});
```

### 3.2. Cấp quyền Content Manager

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/user-management/{{staff_id}}/set_permissions/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{admin_token}}
  ```
- Body:
  ```json
  {
    "can_manage_users": false,
    "can_manage_content": true,
    "can_manage_playlists": false
  }
  ```

**Response**:

```json
{
  "status": "Permissions updated"
}
```

### 3.3. Cấp quyền Playlist Manager

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/user-management/{{staff_id}}/set_permissions/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{admin_token}}
  ```
- Body:
  ```json
  {
    "can_manage_users": false,
    "can_manage_content": false,
    "can_manage_playlists": true
  }
  ```

**Response**:

```json
{
  "status": "Permissions updated"
}
```

### 3.4. Cấp nhiều quyền cùng lúc

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/user-management/{{staff_id}}/set_permissions/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{admin_token}}
  ```
- Body:
  ```json
  {
    "can_manage_users": true,
    "can_manage_content": true,
    "can_manage_playlists": true
  }
  ```

## 4. Test các chức năng của từng loại người dùng

### 4.1. Đăng nhập với Staff User

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/auth/token/`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body:
  ```json
  {
    "email": "staff@example.com",
    "password": "StrongPassword123"
  }
  ```

**Response**:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Test Script**:

```javascript
pm.test("Staff login successful", function () {
  pm.response.to.have.status(200);
  var jsonData = pm.response.json();
  pm.environment.set("staff_token", jsonData.access);
  console.log("Staff token set");
});
```

### 4.2. Test chức năng User Manager

#### 4.2.1. Lấy danh sách người dùng

**Request**:

- Method: `GET`
- URL: `{{base_url}}/api/user-management/`
- Headers:
  ```
  Authorization: Bearer {{staff_token}}
  ```

**Response**:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "admin"
      // Thông tin chi tiết
    },
    {
      "id": 2,
      "username": "staffuser"
      // Thông tin chi tiết
    }
  ]
}
```

#### 4.2.2. Kích hoạt/vô hiệu hóa tài khoản

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/user-management/3/toggle_active/` (ID của một người dùng khác)
- Headers:
  ```
  Authorization: Bearer {{staff_token}}
  ```

**Response**:

```json
{
  "status": "User deactivated"
}
```

#### 4.2.3. Test giới hạn quyền - không thể cấp quyền Staff

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/user-management/3/toggle_staff/`
- Headers:
  ```
  Authorization: Bearer {{staff_token}}
  ```

**Response** (403 Forbidden):

```json
{
  "error": "Only superusers can change staff status"
}
```

### 4.3. Test chức năng Content Manager

#### 4.3.1. Tạo bài hát mới

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/music/songs/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{staff_token}}
  ```
- Body:
  ```json
  {
    "title": "Test Song",
    "artist": "Test Artist",
    "genre": "Pop",
    "file_url": "https://example.com/song.mp3"
  }
  ```

**Response**:

```json
{
  "id": 1,
  "title": "Test Song",
  "artist": "Test Artist",
  "genre": "Pop",
  "file_url": "https://example.com/song.mp3",
  "created_at": "2023-11-01T12:00:00Z"
}
```

#### 4.3.2. Duyệt nội dung

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/music/songs/1/approve/`
- Headers:
  ```
  Authorization: Bearer {{staff_token}}
  ```

**Response**:

```json
{
  "status": "Song approved"
}
```

### 4.4. Test chức năng Playlist Manager

#### 4.4.1. Tạo playlist công cộng

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/music/playlists/`
- Headers:
  ```
  Content-Type: application/json
  Authorization: Bearer {{staff_token}}
  ```
- Body:
  ```json
  {
    "name": "Featured Playlist",
    "description": "A playlist created by staff",
    "is_public": true
  }
  ```

**Response**:

```json
{
  "id": 1,
  "name": "Featured Playlist",
  "description": "A playlist created by staff",
  "is_public": true,
  "created_at": "2023-11-01T12:00:00Z"
}
```

#### 4.4.2. Duyệt playlist người dùng

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/music/playlists/2/approve/` (ID của một playlist người dùng)
- Headers:
  ```
  Authorization: Bearer {{staff_token}}
  ```

**Response**:

```json
{
  "status": "Playlist approved"
}
```

## 5. Test các hạn chế quyền

### 5.1. Regular User không thể truy cập API quản lý

**Request**:

- Method: `GET`
- URL: `{{base_url}}/api/user-management/`
- Headers:
  ```
  Authorization: Bearer {{regular_token}}
  ```

**Response** (403 Forbidden):

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 5.2. Staff không có quyền cụ thể không thể truy cập

**Request**:

- Method: `POST`
- URL: `{{base_url}}/api/user-management/set_permissions/`
- Headers:
  ```
  Authorization: Bearer {{staff_token_without_user_management}}
  ```

**Response** (403 Forbidden):

```json
{
  "detail": "You do not have permission to perform this action."
}
```

## 6. Quy trình phân quyền đầy đủ

Dưới đây là quy trình phân quyền đầy đủ mà bạn có thể test:

1. **Tạo tài khoản Admin** (sử dụng `createsuperuser`)
2. **Tạo Regular User** (đăng ký API)
3. **Admin cấp quyền Staff** cho Regular User
4. **Admin cấp quyền quản lý** cụ thể (User Manager, Content Manager, Playlist Manager)
5. **Staff đăng nhập** và truy cập các API được phân quyền
6. **Staff thực hiện các chức năng quản lý** theo quyền được cấp
7. **Staff không thể truy cập** các API nằm ngoài quyền được cấp
8. **Admin có thể thu hồi quyền** bất cứ lúc nào

## 7. Chức năng chi tiết của mỗi loại người dùng

### 7.1. Admin

- Quản lý tất cả người dùng
- Cấp/thu hồi quyền Staff
- Phân quyền quản lý cho Staff
- Truy cập toàn bộ chức năng trong hệ thống
- Cấu hình hệ thống
- Xem thống kê và báo cáo

### 7.2. User Manager

- Xem danh sách người dùng
- Xem thông tin chi tiết người dùng
- Kích hoạt/vô hiệu hóa tài khoản
- Quản lý thông tin cá nhân người dùng
- Không thể cấp quyền Staff hoặc phân quyền quản lý

### 7.3. Content Manager

- Quản lý bài hát, album
- Thêm, sửa, xóa bài hát
- Duyệt nội dung người dùng đăng tải
- Quản lý thể loại nhạc
- Quản lý nghệ sĩ
- Quản lý bình luận trên bài hát

### 7.4. Playlist Manager

- Tạo và quản lý playlist công cộng
- Duyệt playlist người dùng
- Thêm/xóa bài hát trong playlist công cộng
- Đánh dấu playlist "Featured"
- Quản lý các playlist theo chủ đề

### 7.5. Regular User

- Xem và cập nhật thông tin cá nhân
- Quản lý playlist riêng
- Đăng tải bài hát (cần được duyệt)
- Theo dõi người dùng khác
- Bình luận, đánh giá bài hát
- Tạo playlist riêng tư/công khai

## 8. Postman Collection Full Flow

Để test đầy đủ, bạn có thể tạo một Collection Runner với các bước như sau:

1. Đăng nhập Admin
2. Đăng ký Regular User
3. Admin cấp quyền Staff
4. Admin cấp quyền User Manager
5. Đăng nhập Staff
6. Test các chức năng User Manager
7. Admin cấp quyền Content Manager
8. Test các chức năng Content Manager
9. Admin cấp quyền Playlist Manager
10. Test các chức năng Playlist Manager
11. Admin thu hồi tất cả quyền
12. Test không có quyền truy cập

Thực hiện Collection này sẽ cho phép bạn test toàn bộ quy trình phân quyền trong hệ thống của mình.
