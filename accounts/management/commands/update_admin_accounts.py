from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Cập nhật tài khoản admin, đảm bảo tất cả các admin có is_admin=True và is_staff=True'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Tên người dùng cụ thể để cập nhật quyền admin',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Tự động sửa các tài khoản không nhất quán',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        fix = options.get('fix')
        
        # Lấy tất cả các tài khoản có is_admin=True hoặc is_staff=True
        if username:
            # Nếu có tên người dùng, chỉ kiểm tra tài khoản đó
            try:
                admin_users = [User.objects.get(username=username)]
                self.stdout.write(f"Đang kiểm tra tài khoản: {username}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Không tìm thấy người dùng: {username}"))
                return
        else:
            # Nếu không, kiểm tra tất cả
            admin_users = User.objects.filter(is_admin=True) | User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
            self.stdout.write(f"Tìm thấy {admin_users.count()} tài khoản admin hoặc staff.")
        
        # Kiểm tra và hiển thị thông tin
        issues_found = False
        for user in admin_users:
            self.stdout.write(f"Username: {user.username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"is_admin: {user.is_admin}")
            self.stdout.write(f"is_staff: {user.is_staff}")
            self.stdout.write(f"is_superuser: {user.is_superuser}")
            
            # Kiểm tra sự không nhất quán
            if user.is_superuser and (not user.is_admin or not user.is_staff):
                self.stdout.write(self.style.WARNING(f"CẢNH BÁO: Superuser nhưng thiếu quyền admin hoặc staff!"))
                issues_found = True
            elif user.is_admin and not user.is_staff:
                self.stdout.write(self.style.WARNING(f"CẢNH BÁO: Admin nhưng thiếu quyền staff!"))
                issues_found = True
            
            self.stdout.write("---")
        
        # Chỉ hỏi nếu tìm thấy vấn đề và fix flag không được đặt
        if issues_found and not fix:
            self.stdout.write(self.style.WARNING("Phát hiện các tài khoản không nhất quán."))
            self.stdout.write("Chạy lại lệnh với flag --fix để sửa tự động.")
            return
        
        # Sửa chữa nếu có vấn đề và flag fix được đặt, hoặc nếu có username cụ thể
        if (issues_found and fix) or username:
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
                    elif username and not user.is_admin:  # Nếu chỉ định username, đặt là admin
                        user.is_admin = True
                        user.is_staff = True
                        updated = True
                    
                    if updated:
                        user.save()
                        self.stdout.write(self.style.SUCCESS(f"Đã cập nhật tài khoản {user.username}"))
            
            self.stdout.write(self.style.SUCCESS("Đã hoàn tất cập nhật tài khoản."))
        
        # Hiển thị số lượng tài khoản admin sau khi cập nhật
        admin_count = User.objects.filter(is_admin=True).count()
        self.stdout.write(f"Số lượng tài khoản admin: {admin_count}") 