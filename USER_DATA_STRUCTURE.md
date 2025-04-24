# Cấu Trúc Dữ Liệu Người Dùng

Tài liệu này mô tả chi tiết cách thông tin người dùng được lưu trữ, xử lý và truy cập trong hệ thống.

## 1. Mô Hình Dữ Liệu (Model)

### 1.1 User Model (accounts/models.py)

User là mô hình cốt lõi của hệ thống, kế thừa từ AbstractUser của Django:

#### Thông tin cơ bản

- `id`: Khóa chính, tự động tăng
- `username`: Tên đăng nhập (độc nhất)
- `email`: Email (độc nhất)
- `password`: Mật khẩu (được mã hóa)
- `first_name`: Tên
- `last_name`: Họ
- `avatar`: Ảnh đại diện
- `bio`: Tiểu sử/mô tả

#### Thông tin thời gian

- `date_joined`: Thời gian đăng ký
- `last_login`: Thời gian đăng nhập cuối
- `created_at`: Thời gian tạo
- `updated_at`: Thời gian cập nhật

#### Thông tin phân quyền

- `is_active`: Trạng thái hoạt động
- `is_staff`: Có phải nhân viên
- `is_superuser`: Có phải admin
- `can_manage_users`: Quyền quản lý người dùng
- `can_manage_content`: Quyền quản lý nội dung
- `can_manage_playlists`: Quyền quản lý playlist

#### Quan hệ

- `favorite_songs`: ManyToMany với Song
- `following`: ManyToMany với User (không đối xứng)
- `followers`: Quan hệ ngược với following
- `groups`: Liên kết với Django Groups
- `user_permissions`: Liên kết với Django Permissions

#### Thuộc tính tính toán

- `is_user_manager`: Trả về True nếu là staff và có quyền quản lý người dùng
- `is_content_manager`: Trả về True nếu là staff và có quyền quản lý nội dung
- `is_playlist_manager`: Trả về True nếu là staff và có quyền quản lý playlist

## 2. Cách Thông Tin Được Lưu Trữ Khi Đăng Ký

### 2.1 Quá Trình Đăng Ký (UserRegistrationSerializer)

```python
# POST /api/accounts/auth/register/
{
    "username": "johndoe",
    "email": "johndoe@example.com",
    "password": "secure_password",
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Music lover",
    "avatar": [file_upload]
}
```

1. Dữ liệu được gửi đến endpoint đăng ký
2. `UserRegistrationSerializer` kiểm tra và xác thực dữ liệu
3. Password được mã hóa bằng phương thức `set_password()`
4. Dữ liệu được lưu vào bảng `users` trong cơ sở dữ liệu
5. Default values:
   - `is_active`: True
   - `is_staff`: False
   - `is_superuser`: False
   - `can_manage_users`: False
   - `can_manage_content`: False
   - `can_manage_playlists`: False
   - `date_joined`: Thời gian hiện tại

### 2.2 Quá Trình Đăng Nhập (JWT)

```python
# POST /api/auth/token/
{
    "email": "johndoe@example.com",
    "password": "secure_password"
}
```

1. Người dùng gửi email và password
2. Hệ thống xác thực thông tin
3. JWT token được tạo và trả về
4. Thông tin `last_login` được cập nhật
5. Token chứa:
   - `user_id`: ID của người dùng
   - `exp`: Thời gian hết hạn
   - `iat`: Thời gian phát hành
   - `jti`: JWT ID
   - `token_type`: Loại token (access hoặc refresh)

## 3. Cách Phân Quyền Được Lưu Trữ

### 3.1 Phân Quyền Admin

```python
# Tạo bằng lệnh createsuperuser
python manage.py createsuperuser
```

Thông tin lưu trữ:

- `is_staff`: True
- `is_superuser`: True
- Có tất cả quyền

### 3.2 Phân Quyền Nhân Viên (Staff)

```python
# POST /api/accounts/user-management/{id}/toggle_staff/
# (Chỉ Admin mới thực hiện được)
```

Thông tin lưu trữ:

- `is_staff`: True
- `is_superuser`: False

### 3.3 Phân Quyền Chi Tiết (Permissions)

```python
# POST /api/accounts/user-management/{id}/set_permissions/
# (Chỉ Admin mới thực hiện được)
{
    "can_manage_users": true,
    "can_manage_content": true,
    "can_manage_playlists": false
}
```

Thông tin lưu trữ trong bảng `users`:

- `can_manage_users`: Boolean
- `can_manage_content`: Boolean
- `can_manage_playlists`: Boolean

## 4. Cách Truy Cập Thông Tin Người Dùng

### 4.1 Serializers cho Các Trường Hợp Khác Nhau

#### UserSerializer (Thông tin cơ bản)

```python
fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'bio')
```

#### PublicUserSerializer (Thông tin công khai)

```python
fields = ('id', 'username', 'avatar', 'bio')
```

#### AdminUserSerializer (Thông tin quản lý)

```python
fields = (
    'id', 'username', 'email', 'first_name', 'last_name',
    'avatar', 'bio', 'is_active', 'is_staff', 'is_superuser',
    'date_joined', 'last_login', 'can_manage_users',
    'can_manage_content', 'can_manage_playlists',
    'followers_count', 'following_count'
)
```

#### CompleteUserSerializer (Tất cả thông tin)

```python
fields = (
    'id', 'username', 'email', 'first_name', 'last_name',
    'avatar', 'bio', 'is_active', 'is_staff', 'is_superuser',
    'date_joined', 'last_login', 'can_manage_users',
    'can_manage_content', 'can_manage_playlists',
    'followers_count', 'following_count', 'followers', 'following',
    'favorite_songs', 'playlists', 'activities', 'created_at', 'updated_at'
)
```

### 4.2 Endpoints Truy Cập Thông Tin Người Dùng

#### Thông tin cá nhân

```
GET /api/accounts/users/me/
```

#### Danh sách người dùng (Tất cả)

```
GET /api/accounts/users/
```

#### Danh sách người dùng công khai

```
GET /api/accounts/public/users/
```

#### Thông tin người dùng đầy đủ (Admin/Manager)

```
GET /api/accounts/user-management/{id}/complete/
```

## 5. Quản Lý Phiên và Đăng Xuất

### 5.1 Đăng Xuất

```python
# POST /api/accounts/auth/logout/
{
    "refresh": "refresh_token_value"
}
```

1. Token refresh được gửi kèm request
2. Token được kiểm tra có thuộc về người dùng hiện tại
3. Token được đưa vào blacklist để vô hiệu hóa
4. Session được kết thúc

## 6. Hoạt Động Người Dùng (UserActivity)

### 6.1 Lưu Trữ Hoạt Động

```python
UserActivity(
    user=user,
    activity_type='PLAY',
    song=song,
    timestamp=now()
).save()
```

Các loại hoạt động:

- `PLAY`: Phát nhạc
- `LIKE`: Thích bài hát
- `FOLLOW`: Theo dõi người dùng
- `CREATE_PLAYLIST`: Tạo playlist
- `ADD_TO_PLAYLIST`: Thêm bài hát vào playlist

## 7. Lưu Trữ Lịch Sử Phát Nhạc

```python
SongPlayHistory(
    user=user,
    song=song,
    played_at=now()
).save()
```

Mỗi lần người dùng phát nhạc, một bản ghi được lưu trong bảng `song_play_history`.
