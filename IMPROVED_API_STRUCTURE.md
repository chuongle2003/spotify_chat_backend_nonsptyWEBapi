# Cải Tiến Cấu Trúc API

Tài liệu này trình bày chi tiết về những cải tiến được đề xuất cho cấu trúc API của hệ thống, nhằm tạo ra một API nhất quán, dễ hiểu và tuân theo các tiêu chuẩn thiết kế RESTful.

## 1. Nguyên Tắc Thiết Kế

### 1.1 Nhất Quán và Tổ Chức

- **Phân Cấp Rõ Ràng**: Sử dụng cấu trúc `/api/[module]/[resource]/[action]/`
- **Nhóm Theo Chức Năng**: Các endpoints có chức năng liên quan được nhóm lại với nhau
- **Đường Dẫn Mô Tả**: URLs phải mô tả rõ ràng tài nguyên và hành động

### 1.2 Quy Ước Đặt Tên

- **Sử Dụng Danh Từ Số Nhiều**: Cho các collection (ví dụ: `/users/` thay vì `/user/`)
- **Kebab-Case Cho URLs**: Sử dụng dấu gạch ngang cho URLs (ví dụ: `/user-management/`)
- **CamelCase Cho Tham Số**: Sử dụng camelCase cho tham số JSON (ví dụ: `firstName`)

### 1.3 Versioning và Mở Rộng

- **API Versioning**: Sử dụng `/api/v1/` để hỗ trợ nâng cấp trong tương lai
- **Tham Số Mở Rộng**: Hỗ trợ các tham số như `?fields=`, `?embed=` để tối ưu dữ liệu trả về

## 2. Cấu Trúc URL Mới

### 2.1 Cấu Trúc Tổng Thể

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
│   ├── playlists/         # CRUD playlist
│   ├── albums/            # CRUD album
│   └── comments/          # CRUD bình luận
│
└── chat/                  # Quản lý chat
    ├── messages/          # CRUD tin nhắn
    └── conversations/     # Quản lý cuộc trò chuyện
```

### 2.2 Endpoints Xác Thực Được Cập Nhật

| Endpoint Cũ                    | Endpoint Mới                      | Mô Tả         |
| ------------------------------ | --------------------------------- | ------------- |
| `/api/token/`                  | `/api/v1/auth/token/`             | Lấy JWT token |
| `/api/token/refresh/`          | `/api/v1/auth/token/refresh/`     | Làm mới token |
| `/api/accounts/auth/logout/`   | `/api/v1/auth/logout/`            | Đăng xuất     |
| `/api/accounts/auth/register/` | `/api/v1/accounts/auth/register/` | Đăng ký       |

### 2.3 Endpoints Quản Lý Người Dùng Được Cập Nhật

| Endpoint Cũ                      | Endpoint Mới                         | Mô Tả                          |
| -------------------------------- | ------------------------------------ | ------------------------------ |
| `/api/accounts/users/`           | `/api/v1/accounts/users/`            | Quản lý người dùng cơ bản      |
| `/api/accounts/users/me/`        | `/api/v1/accounts/users/me/`         | Thông tin người dùng hiện tại  |
| `/api/accounts/public/users/`    | `/api/v1/accounts/public/users/`     | Danh sách người dùng công khai |
| `/api/accounts/admin/users/`     | `/api/v1/accounts/admin/users/`      | Quản lý người dùng (admin)     |
| `/api/accounts/user-management/` | `/api/v1/accounts/management/users/` | Quản lý người dùng (staff)     |

## 3. Thay Đổi Chi Tiết

### 3.1 Cập Nhật backend/urls.py

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from accounts.views import LogoutView  # Import LogoutView từ accounts

# API v1 patterns
api_v1_patterns = [
    # Auth endpoints
    path('auth/', include([
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('logout/', LogoutView.as_view(), name='logout'),
    ])),

    # Module endpoints
    path('accounts/', include('accounts.urls')),
    path('music/', include('music.urls')),
    path('chat/', include('chat.urls')),
]

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include(api_v1_patterns)),

    # Legacy support (tùy chọn, để duy trì tương thích ngược)
    path('api/', include(api_v1_patterns)),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 3.2 Cập Nhật accounts/urls.py

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'admin/users', views.AdminViewSet)
router.register(r'management/users', views.UserManagementViewSet, basename='user-management')

urlpatterns = [
    # Bao gồm tất cả router URLs
    path('', include(router.urls)),

    # Authentication endpoints
    path('auth/', include([
        path('register/', views.RegisterView.as_view(), name='register'),
        # LogoutView đã được chuyển lên /api/v1/auth/logout/
    ])),

    # Public endpoints
    path('public/', include([
        path('users/', views.PublicUserListView.as_view(), name='public-users'),
    ])),
]
```

### 3.3 Di Chuyển Và Cập Nhật Tài Liệu API

Cập nhật tất cả các tài liệu API để phản ánh cấu trúc mới, bao gồm:

- API_SPECIFICATION.md
- API_IMPLEMENTATION_GUIDE.md
- API_DETAILS.md (nếu có)

## 4. Lợi Ích Và Ưu Điểm

### 4.1 Cải Thiện Trải Nghiệm Nhà Phát Triển

- **Dễ Đoán**: Cấu trúc nhất quán giúp dễ đoán endpoints
- **Tự Giải Thích**: URLs mô tả rõ ràng tài nguyên và hành động
- **Dễ Khám Phá**: Cấu trúc phân cấp giúp khám phá API dễ dàng hơn

### 4.2 Khả Năng Bảo Trì Và Mở Rộng

- **Tổ Chức Tốt Hơn**: Phân tách rõ ràng giữa xác thực và quản lý tài nguyên
- **Versioning**: Hỗ trợ sẵn cho việc thêm phiên bản API mới
- **Dễ Mở Rộng**: Cấu trúc mô-đun hóa giúp dễ thêm tính năng mới

### 4.3 Bảo Mật Cải Thiện

- **Phân Quyền Rõ Ràng**: Cấu trúc endpoints phản ánh mô hình phân quyền
- **Tách Biệt Auth**: Tách riêng logic xác thực ra khỏi các modules

## 5. Chiến Lược Triển Khai

### 5.1 Kế Hoạch Di Chuyển

1. **Thêm Phiên Bản Mới**: Triển khai `/api/v1/` song song với endpoints hiện tại
2. **Duy Trì Tương Thích Ngược**: Giữ endpoints cũ trong thời gian chuyển tiếp
3. **Thông Báo Kế Hoạch Hết Hạn**: Đặt lịch trình rõ ràng khi endpoints cũ sẽ bị loại bỏ

### 5.2 Cập Nhật Tài Liệu

- Cập nhật tất cả tài liệu API để phản ánh cấu trúc mới
- Cung cấp hướng dẫn di chuyển cho nhà phát triển
- Thêm ví dụ sử dụng các endpoints mới

### 5.3 Giám Sát Và Điều Chỉnh

- Giám sát việc sử dụng endpoints mới so với endpoints cũ
- Thu thập phản hồi từ nhà phát triển và điều chỉnh nếu cần
- Thực hiện kiểm tra hiệu suất để đảm bảo cấu trúc mới hoạt động tốt
