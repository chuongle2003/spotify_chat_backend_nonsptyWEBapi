import os
import sys
import django

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def create_admin_user(username, email, password):
    """
    Tạo một tài khoản admin mới với đầy đủ quyền
    """
    try:
        with transaction.atomic():
            # Kiểm tra xem user đã tồn tại hay chưa
            if User.objects.filter(username=username).exists():
                print(f"Người dùng {username} đã tồn tại, đang cập nhật quyền admin...")
                user = User.objects.get(username=username)
                user.is_admin = True
                user.is_staff = True
                user.set_password(password)
                user.save()
                print(f"Đã cập nhật quyền admin cho {username}")
            else:
                # Tạo user mới
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_admin=True,
                    is_staff=True
                )
                print(f"Đã tạo tài khoản admin mới: {username}")
            
            # Kiểm tra xác nhận
            user = User.objects.get(username=username)
            print(f"Thông tin tài khoản admin:")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"is_admin: {user.is_admin}")
            print(f"is_staff: {user.is_staff}")
            print(f"is_superuser: {user.is_superuser}")
        
        return True
    except Exception as e:
        print(f"Lỗi khi tạo tài khoản admin: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Sử dụng: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    success = create_admin_user(username, email, password)
    
    if success:
        print("Hoàn tất!")
    else:
        print("Có lỗi xảy ra, vui lòng kiểm tra lại.")
        sys.exit(1) 