from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Vấn đề có thể ở đây - class admin tùy chỉnh đang cố hiển thị trường has_spotify
class CustomUserAdmin(UserAdmin):
    # Thay đổi list_display để bỏ trường has_spotify
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    # Hoặc nếu có fieldsets tùy chỉnh, cũng cần kiểm tra và xóa trường has_spotify

# Thay thế dòng này:
# admin.site.register(User, CustomUserAdmin)
# bằng:
admin.site.register(User, UserAdmin)  # Sử dụng UserAdmin mặc định
