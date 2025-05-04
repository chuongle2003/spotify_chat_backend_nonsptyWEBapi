#!/usr/bin/env python
"""
Script chính để tạo toàn bộ dữ liệu mẫu cho hệ thống Spotify Chat
1. Tạo dữ liệu cơ bản (user, song, genre, playlist)
2. Tạo dữ liệu xã hội (following, chat)
"""

import os
import sys
import time
import django

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import các module tạo dữ liệu
from seed_core_data import run_all as run_core_data
from seed_social_data import run_all as run_social_data

def main():
    """Hàm chính để chạy tất cả các script tạo dữ liệu"""
    print("=" * 80)
    print("KHỞI TẠO DỮ LIỆU MẪU CHO HỆ THỐNG SPOTIFY CHAT")
    print("=" * 80)
    
    # Tạo dữ liệu cơ bản
    print("\n1. TẠO DỮ LIỆU CƠ BẢN\n" + "-" * 30)
    start_time = time.time()
    run_core_data()
    core_time = time.time() - start_time
    print(f"Hoàn thành tạo dữ liệu cơ bản trong {core_time:.2f} giây\n")
    
    # Tạo dữ liệu xã hội
    print("\n2. TẠO DỮ LIỆU XÃ HỘI\n" + "-" * 30)
    start_time = time.time()
    run_social_data()
    social_time = time.time() - start_time
    print(f"Hoàn thành tạo dữ liệu xã hội trong {social_time:.2f} giây\n")
    
    # Tổng kết
    total_time = core_time + social_time
    print("=" * 80)
    print(f"HOÀN THÀNH TẠO DỮ LIỆU MẪU TRONG {total_time:.2f} GIÂY")
    print("=" * 80)
    
    print("\nTHÔNG TIN ĐĂNG NHẬP MẶC ĐỊNH:")
    print("- Admin: email=admin@example.com, password=Admin123!")
    print("- User thường: email=user1@example.com, password=Password123!")
    print("\nSử dụng API mới tại các endpoint:")
    print("- Danh sách người đang theo dõi: GET /api/v1/accounts/social/following/")
    print("- Danh sách người theo dõi: GET /api/v1/accounts/social/followers/")
    print("- Tìm kiếm người dùng: GET /api/v1/accounts/social/search/?q=tên")
    print("- Gợi ý người dùng: GET /api/v1/accounts/social/recommendations/")
    print("- Theo dõi người dùng: POST /api/v1/accounts/social/follow/{user_id}/")
    print("- Hủy theo dõi: POST /api/v1/accounts/social/unfollow/{user_id}/")
    
if __name__ == "__main__":
    main() 