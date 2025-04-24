from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_admin', 'is_active')
    list_filter = ('is_admin', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('email',)
    
    # Tùy chỉnh fieldsets để thêm role và loại bỏ is_staff/is_superuser
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'avatar', 'bio')}),
        ('Permissions', {'fields': ('is_admin', 'is_active')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Tùy chỉnh add_fieldsets để thêm role và loại bỏ is_staff/is_superuser
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_admin', 'is_active'),
        }),
    )
