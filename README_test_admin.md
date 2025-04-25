# Admin Testing Guide

This guide explains how to test the admin functionality, create an admin account, and manage user permissions for the Spotify Chat API.

## Setting Up Environment Variables

1. Import the included Postman environment file (`POSTMAN_ENV.json`) to set up the testing environment
2. Import the included Postman collection file (`POSTMAN_COLLECTION.json`) to load all API endpoints

## Creating an Admin Account

You can create an admin account in two ways:

### Method 1: Using Django Command Line

```bash
python manage.py createsuperuser
```

Follow the prompts to enter email, username, and password.

### Method 2: Using existing admin to promote a user (requires an admin token)

1. Register a regular user first:

   ```
   POST {{base_url}}/api/accounts/auth/register/
   Body:
   {
     "email": "newadmin@example.com",
     "username": "newadmin",
     "password": "securePassword123",
     "first_name": "New",
     "last_name": "Admin"
   }
   ```

2. Login as an existing admin:

   ```
   POST {{base_url}}/api/auth/token/
   Body:
   {
     "email": "admin@example.com",
     "password": "adminPassword123"
   }
   ```

3. Make the user a staff member:

   ```
   POST {{base_url}}/api/user-management/{{user_id}}/toggle_staff/
   Headers: Authorization: Bearer {{admin_token}}
   Body: { "is_staff": true }
   ```

4. Make the user a superuser:
   ```
   POST {{base_url}}/api/user-management/{{user_id}}/toggle_superuser/
   Headers: Authorization: Bearer {{admin_token}}
   Body: { "is_superuser": true }
   ```

## Getting Admin Token

To use admin API endpoints, you need to obtain a token:

```
POST {{base_url}}/api/auth/token/
Body:
{
  "email": "admin@example.com",
  "password": "adminPassword123"
}
```

Save the received token in your Postman environment variable `token`.

## Testing Admin Permissions

### Viewing All Users (Admin Only)

```
GET {{base_url}}/api/user-management/users/
Headers: Authorization: Bearer {{token}}
```

### Creating Staff Users with Specific Permissions

1. Register a regular user
2. Make them a staff member (see above)
3. Assign specific permissions:
   ```
   POST {{base_url}}/api/user-management/{{staff_id}}/set_permissions/
   Headers: Authorization: Bearer {{admin_token}}
   Body:
   {
     "can_manage_users": true,
     "can_manage_content": false,
     "can_manage_playlists": true
   }
   ```

### Permission Test Matrix

Test the following scenarios with different user types:

| Action                 | Regular User | User Manager | Content Manager | Playlist Manager | Admin |
| ---------------------- | ------------ | ------------ | --------------- | ---------------- | ----- |
| View profile           | ✓            | ✓            | ✓               | ✓                | ✓     |
| Edit own profile       | ✓            | ✓            | ✓               | ✓                | ✓     |
| View all users         | ✗            | ✓            | ✗               | ✗                | ✓     |
| Edit other users       | ✗            | ✓            | ✗               | ✗                | ✓     |
| Upload songs           | ✗            | ✗            | ✓               | ✗                | ✓     |
| Edit songs             | ✗            | ✗            | ✓               | ✗                | ✓     |
| Create playlists       | ✓            | ✓            | ✓               | ✓                | ✓     |
| Feature playlists      | ✗            | ✗            | ✗               | ✓                | ✓     |
| Manage system settings | ✗            | ✗            | ✗               | ✗                | ✓     |

## Admin Account Fields

When viewing an admin account through the API, you'll see these fields:

- `id`: Unique identifier
- `username`: Admin username
- `email`: Admin email address
- `first_name`, `last_name`: Personal information
- `avatar`: Profile picture URL
- `bio`: Admin biography
- `is_active`: Account status
- `is_staff`: Staff status (true for admins)
- `is_superuser`: Superuser status (true for admins)
- `can_manage_users`, `can_manage_content`, `can_manage_playlists`: Permission flags
- `date_joined`: Account creation date
- `last_login`: Last authentication time
- `followers_count`, `following_count`: Social statistics

Note: Password information is never returned in API responses for security reasons.

## Test Automation

Use Postman collection runner to automate testing:

1. Set up environment variables
2. Configure the collection runner with the following test flow:
   - Create admin account
   - Get admin token
   - Register test users
   - Assign different permission levels
   - Test functionality for each user type
   - Verify expected access levels

## Troubleshooting

- If you receive a 403 Forbidden response, check the token and user permissions
- If admin creation fails, ensure the database is properly migrated:
  ```bash
  python manage.py migrate
  ```
- For token issues, verify the token hasn't expired and you're using the proper format in the Authorization header

## Hướng dẫn Test Quyền Admin

File này cung cấp hướng dẫn kiểm tra các quyền và chức năng dành cho Admin trong ứng dụng Spotify Chat API.

### Chuẩn bị

1. Đảm bảo API đã được khởi chạy (`python manage.py runserver`)
2. Import collection và environment từ Postman
3. Đăng nhập với tài khoản admin để lấy token

### Kiểm tra quyền cơ bản

#### Đăng nhập Admin

1. Sử dụng request "Login - Get Token" với tài khoản admin
2. Kiểm tra response có chứa trường `is_admin` với giá trị `true`
3. Token sẽ được tự động lưu vào biến môi trường

#### Truy cập API chỉ dành cho Admin

1. Sử dụng request "List All Users"
2. Kiểm tra status code là 200 và nhận được danh sách người dùng
3. Đăng xuất và đăng nhập lại với tài khoản không phải admin
4. Thử lại request "List All Users", kiểm tra status code là 403 (Forbidden)

### Quản lý người dùng (Admin)

#### Lấy danh sách người dùng

1. Sử dụng request "List All Users"
2. Kiểm tra danh sách người dùng đầy đủ thông tin

#### Tạo người dùng mới

1. Sử dụng request "Create User"
2. Điền thông tin người dùng mới trong body
3. Kiểm tra response có status code 201 và chứa thông tin người dùng mới
4. Có thể tạo người dùng thường hoặc admin bằng cách đặt `is_admin: true`

#### Xem thông tin chi tiết người dùng

1. Lấy ID của người dùng từ danh sách
2. Điền ID vào biến `target_user_id`
3. Sử dụng request "Get User Details"
4. Để xem thông tin chi tiết hơn bao gồm hoạt động, bài hát yêu thích, v.v., sử dụng request "Get User Complete Profile"

#### Cập nhật thông tin người dùng

1. Đặt `target_user_id` cho người dùng cần cập nhật
2. Sử dụng request "Update User"
3. Điền thông tin cần cập nhật trong body
4. Kiểm tra response có status code 200 và thông tin đã được cập nhật

#### Xóa người dùng

1. Đặt `target_user_id` cho người dùng cần xóa
2. Sử dụng request "Delete User"
3. Kiểm tra status code là 204 (No Content)
4. Thử lấy thông tin người dùng đã xóa để đảm bảo người dùng không còn tồn tại

#### Thay đổi trạng thái kích hoạt của người dùng

1. Đặt `target_user_id` cho người dùng cần thay đổi
2. Sử dụng request "Toggle User Active Status"
3. Kiểm tra response có thông báo về việc người dùng đã được kích hoạt hoặc vô hiệu hóa
4. Kiểm tra lại trạng thái của người dùng

#### Thay đổi quyền Admin

1. Đặt `target_user_id` cho người dùng cần thay đổi
2. Sử dụng request "Toggle Admin Status"
3. Kiểm tra response có thông báo về việc cấp hoặc thu hồi quyền admin
4. Kiểm tra lại trạng thái của người dùng

### Chức năng quản lý nội dung (Admin)

#### Tải lên bài hát mới

1. Sử dụng request "Upload Song" trong thư mục Music Management
2. Điền thông tin bài hát và đính kèm file audio và hình ảnh
3. Kiểm tra response có status code 201 và chứa thông tin bài hát mới

#### Chỉnh sửa bài hát

1. Đăng nhập với tài khoản admin
2. Lấy ID bài hát và đặt vào biến `song_id`
3. Sử dụng request PUT với endpoint `/api/v1/music/songs/{song_id}/`
4. Kiểm tra chỉ admin mới có thể chỉnh sửa bài hát

#### Xóa bài hát

1. Đăng nhập với tài khoản admin
2. Lấy ID bài hát và đặt vào biến `song_id`
3. Sử dụng request DELETE với endpoint `/api/v1/music/songs/{song_id}/`
4. Kiểm tra chỉ admin mới có thể xóa bài hát

### Kiểm tra phân quyền

#### Thử truy cập API Admin với người dùng thường

1. Đăng xuất và đăng nhập lại với tài khoản không phải admin
2. Thử các request dành cho admin
3. Kiểm tra tất cả đều trả về status code 403 (Forbidden)

#### Đổi quyền cho người dùng

1. Đăng nhập với tài khoản admin
2. Đặt `target_user_id` cho một người dùng thường
3. Sử dụng request "Toggle Admin Status"
4. Đăng xuất và đăng nhập với tài khoản vừa được cấp quyền admin
5. Kiểm tra các request dành cho admin đều hoạt động

### Lưu ý về bảo mật

- Đảm bảo chỉ admin mới có thể thực hiện các hành động quản trị
- Kiểm tra kỹ lưỡng các API endpoint để đảm bảo không lộ thông tin nhạy cảm
- API nên sử dụng HTTPS khi triển khai thực tế
- Kiểm tra việc lưu trữ và sử dụng token JWT đúng cách
