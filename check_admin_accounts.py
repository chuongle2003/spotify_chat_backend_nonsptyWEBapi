import os
import django

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def check_admin_accounts():
    """
    Kiểm tra và đảm bảo tất cả các tài khoản admin có cả hai thuộc tính is_admin=True và is_staff=True
    """
    # Lấy tất cả các tài khoản có is_admin=True hoặc is_staff=True
    admin_users = User.objects.filter(is_admin=True) | User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
    
    print(f"Tìm thấy {admin_users.count()} tài khoản admin hoặc staff.")
    
    # Hiển thị thông tin về các tài khoản
    for i, user in enumerate(admin_users, 1):
        print(f"\n{i}. Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   is_admin: {user.is_admin}")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_superuser: {user.is_superuser}")
        
        # Kiểm tra nếu có sự không nhất quán
        if user.is_superuser and (not user.is_admin or not user.is_staff):
            print(f"   CẢNH BÁO: Superuser nhưng thiếu quyền admin hoặc staff!")
        elif user.is_admin and not user.is_staff:
            print(f"   CẢNH BÁO: Admin nhưng thiếu quyền staff!")
    
    # Hỏi người dùng có muốn sửa chữa các tài khoản không nhất quán không
    fix_accounts = input("\nBạn có muốn sửa chữa các tài khoản không nhất quán? (y/n): ")
    
    if fix_accounts.lower() == 'y':
        with transaction.atomic():
            for user in admin_users:
                updated = False
                
                # Cập nhật các tài khoản không nhất quán
                if user.is_superuser:
                    if not user.is_admin or not user.is_staff:
                        user.is_admin = True
                        user.is_staff = True
                        updated = True
                elif user.is_admin and not user.is_staff:
                    user.is_staff = True
                    updated = True
                
                if updated:
                    user.save()
                    print(f"Đã cập nhật tài khoản {user.username}")
        
        print("\nĐã hoàn tất cập nhật tài khoản.")
    else:
        print("\nKhông thực hiện cập nhật nào.")
    
    # Hiển thị số lượng tài khoản admin sau khi cập nhật
    admin_count = User.objects.filter(is_admin=True).count()
    print(f"\nSố lượng tài khoản admin: {admin_count}")

if __name__ == "__main__":
    check_admin_accounts() 