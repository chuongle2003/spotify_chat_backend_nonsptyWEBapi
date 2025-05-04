#!/usr/bin/env python
"""
Script tự động tạo kết nối giữa tất cả người dùng trong hệ thống
Tạo kết nối trạng thái ACCEPTED cho tất cả cặp người dùng để hỗ trợ chat
"""

import os
import sys
import django
import itertools
import time

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import UserConnection
from django.db.models import Q

User = get_user_model()

def create_auto_connections():
    """Tạo kết nối tự động giữa tất cả người dùng với trạng thái ACCEPTED"""
    print("=" * 80)
    print("TẠO KẾT NỐI TỰ ĐỘNG GIỮA TẤT CẢ NGƯỜI DÙNG")
    print("=" * 80)
    
    start_time = time.time()
    
    # Lấy tất cả người dùng
    users = User.objects.all()
    total_users = users.count()
    
    if total_users < 2:
        print("Cần ít nhất 2 người dùng để tạo kết nối!")
        return
    
    print(f"Tìm thấy {total_users} người dùng trong hệ thống")
    
    # Tạo các cặp người dùng (không trùng lặp)
    user_pairs = list(itertools.combinations(users, 2))
    total_pairs = len(user_pairs)
    
    print(f"Sẽ tạo kết nối giữa {total_pairs} cặp người dùng")
    
    # Đếm số lượng kết nối đã tồn tại
    existing_connections = 0
    new_connections = 0
    
    # Sử dụng transaction để tăng tốc và đảm bảo tính nhất quán
    with transaction.atomic():
        # Duyệt qua từng cặp người dùng
        for i, (user1, user2) in enumerate(user_pairs):
            # Hiển thị tiến trình
            if (i + 1) % 10 == 0 or (i + 1) == total_pairs:
                print(f"Đang xử lý: {i + 1}/{total_pairs} cặp ({((i + 1) / total_pairs * 100):.1f}%)")
            
            # Kiểm tra xem đã có kết nối chưa
            connection = UserConnection.get_connection(user1, user2)
            
            if connection:
                # Nếu đã có kết nối, cập nhật thành ACCEPTED
                if connection.status != 'ACCEPTED':
                    connection.status = 'ACCEPTED'
                    connection.save()
                existing_connections += 1
            else:
                # Tạo kết nối mới với trạng thái ACCEPTED
                UserConnection.objects.create(
                    requester=user1,
                    receiver=user2,
                    status='ACCEPTED'
                )
                new_connections += 1
    
    # Tổng kết
    duration = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"HOÀN THÀNH TẠO KẾT NỐI TRONG {duration:.2f} GIÂY")
    print(f"- Số kết nối đã tồn tại: {existing_connections}")
    print(f"- Số kết nối mới tạo: {new_connections}")
    print(f"- Tổng số kết nối: {existing_connections + new_connections}")
    print("=" * 80)
    
    print("\nTất cả người dùng trong hệ thống giờ đây có thể chat với nhau!")
    print("Lưu ý: Kết nối này chỉ là tùy chọn vì hệ thống đã được cấu hình để cho phép người dùng chat mà không cần kiểm tra kết nối.")

if __name__ == "__main__":
    create_auto_connections() 