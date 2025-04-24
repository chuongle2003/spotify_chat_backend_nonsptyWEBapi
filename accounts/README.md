# Hướng dẫn phân quyền trong hệ thống

## Các loại người dùng

Hệ thống phân quyền gồm các loại người dùng sau:

1. **Regular User**: Người dùng thông thường

   - Xem thông tin cá nhân
   - Cập nhật thông tin cá nhân
   - Tạo và quản lý playlist riêng
   - Theo dõi người dùng khác
   - Bình luận và đánh giá bài hát

2. **Staff User**: Nhân viên hệ thống

   - Có tất cả quyền của Regular User
   - Có thêm các quyền tùy theo vai trò được phân công

3. **Content Manager**: Quản lý nội dung

   - Có tất cả quyền của Staff User
   - Quản lý bài hát, album
   - Duyệt bình luận
   - Quản lý các nội dung công cộng

4. **User Manager**: Quản lý người dùng

   - Có tất cả quyền của Staff User
   - Kích hoạt/vô hiệu hóa tài khoản người dùng
   - Xem thông tin chi tiết người dùng
   - Quản lý thông tin người dùng

5. **Playlist Manager**: Quản lý playlist

   - Có tất cả quyền của Staff User
   - Quản lý playlist công cộng
   - Duyệt playlist của người dùng

6. **Admin**: Quản trị viên
   - Có tất cả các quyền trong hệ thống
   - Phân quyền cho các staff
   - Quản lý cấu hình hệ thống

## Các endpoint phân quyền

### Public (Không cần đăng nhập)

- `GET /api/public/users/`: Danh sách người dùng công khai
- `POST /api/auth/register/`: Đăng ký người dùng mới
- `POST /api/token/`: Lấy token đăng nhập

### Regular User

- `GET, PUT, PATCH /api/users/me/`: Xem và cập nhật thông tin cá nhân
- `POST /api/users/{id}/follow/`: Theo dõi người dùng
- `POST /api/users/{id}/unfollow/`: Hủy theo dõi người dùng
- `POST /api/auth/logout/`: Đăng xuất

### User Manager

- `GET, PUT, PATCH, DELETE /api/user-management/`: Quản lý người dùng
- `POST /api/user-management/{id}/toggle_active/`: Kích hoạt/vô hiệu hóa tài khoản

### Admin

- `GET, PUT, PATCH, DELETE /api/admin/users/`: Quản lý người dùng (admin)
- `POST /api/user-management/{id}/toggle_staff/`: Cấp/thu hồi quyền staff
- `POST /api/user-management/{id}/set_permissions/`: Phân quyền cho staff

## Cài đặt quyền mới

### 1. Thêm trường quyền mới

Mở file `accounts/models.py` và thêm trường quyền mới:

```python
class User(AbstractUser):
    # Các trường hiện có

    # Thêm trường quyền mới
    can_manage_new_feature = models.BooleanField(default=False, verbose_name='Có thể quản lý tính năng mới')

    # Thêm property để kiểm tra
    @property
    def is_new_feature_manager(self):
        return self.is_staff and self.can_manage_new_feature
```

### 2. Tạo migration và áp dụng:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Thêm permission class mới:

Mở file `accounts/permissions.py` và thêm class mới:

```python
class IsNewFeatureManager(permissions.BasePermission):
    """
    Quyền quản lý tính năng mới
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff and request.user.can_manage_new_feature)
```

### 4. Tạo ViewSet mới:

Mở file `accounts/views.py` và thêm ViewSet mới:

```python
class NewFeatureViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho tính năng mới
    """
    permission_classes = [IsNewFeatureManager]
    # Implement the rest of the ViewSet
```

### 5. Đăng ký endpoint mới:

Mở file `urls.py` và đăng ký ViewSet:

```python
router.register(r'new-feature', views.NewFeatureViewSet)
```

## Kiểm tra quyền trong template

Ví dụ kiểm tra quyền trong template Django:

```html
{% if is_admin %}
<a href="/admin">Admin Dashboard</a>
{% endif %} {% if can_manage_content %}
<a href="/content">Quản lý nội dung</a>
{% endif %} {% if can_manage_users %}
<a href="/users">Quản lý người dùng</a>
{% endif %}
```

## Kiểm tra quyền trong React/Frontend

Ví dụ kiểm tra quyền trong React:

```jsx
const UserManagementButton = () => {
  const { user } = useAuth();

  if (!user || !user.permissions || !user.permissions.can_manage_users) {
    return null;
  }

  return (
    <Button onClick={() => navigate("/user-management")}>
      Quản lý người dùng
    </Button>
  );
};
```
