from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Tạo tài khoản admin mới với đầy đủ quyền'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Tên đăng nhập của admin')
        parser.add_argument('email', type=str, help='Email của admin')
        parser.add_argument('password', type=str, help='Mật khẩu của admin')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        try:
            with transaction.atomic():
                # Kiểm tra xem user đã tồn tại hay chưa
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.WARNING(f"Người dùng {username} đã tồn tại, đang cập nhật quyền admin..."))
                    user = User.objects.get(username=username)
                    user.is_admin = True
                    user.is_staff = True
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Đã cập nhật quyền admin cho {username}"))
                else:
                    # Tạo user mới
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        is_admin=True,
                        is_staff=True
                    )
                    self.stdout.write(self.style.SUCCESS(f"Đã tạo tài khoản admin mới: {username}"))
                
                # Kiểm tra xác nhận
                user = User.objects.get(username=username)
                self.stdout.write("Thông tin tài khoản admin:")
                self.stdout.write(f"Username: {user.username}")
                self.stdout.write(f"Email: {user.email}")
                self.stdout.write(f"is_admin: {user.is_admin}")
                self.stdout.write(f"is_staff: {user.is_staff}")
                self.stdout.write(f"is_superuser: {user.is_superuser}")
            
            self.stdout.write(self.style.SUCCESS("Hoàn tất!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Lỗi khi tạo tài khoản admin: {str(e)}"))
            raise 