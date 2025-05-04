#!/usr/bin/env python
"""
Script để tạo dữ liệu social dựa trên dữ liệu người dùng và bài hát hiện có
- Tạo mối quan hệ follow giữa người dùng
- Thêm bài hát yêu thích cho người dùng
- Tạo tin nhắn giữa người dùng
"""

import os
import sys
import django
import random
from datetime import timedelta
import time

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from music.models import Song
from django.utils import timezone
from chat.models import Message

User = get_user_model()

def create_following_relationships():
    """Tạo mối quan hệ theo dõi giữa người dùng dựa trên dữ liệu hiện có"""
    print("Đang tạo mối quan hệ theo dõi...")
    
    # Xóa tất cả mối quan hệ theo dõi hiện có
    for user in User.objects.all():
        user.following.clear()
    
    users = User.objects.all()
    
    if users.count() < 3:
        print("Cần ít nhất 3 người dùng để tạo mối quan hệ theo dõi")
        return
    
    # Mỗi người dùng sẽ theo dõi 30-70% người dùng khác ngẫu nhiên
    total_relationships = 0
    
    for user in users:
        # Loại bỏ người dùng hiện tại
        other_users = users.exclude(id=user.id)
        
        # Tính số lượng người dùng sẽ theo dõi
        num_to_follow = max(1, random.randint(int(other_users.count() * 0.3), int(other_users.count() * 0.7)))
        users_to_follow = random.sample(list(other_users), num_to_follow)
        
        # Theo dõi người dùng
        for user_to_follow in users_to_follow:
            user.following.add(user_to_follow)
            total_relationships += 1
    
    print(f"Đã tạo {total_relationships} mối quan hệ theo dõi giữa {users.count()} người dùng")

def add_favorite_songs():
    """Thêm bài hát yêu thích cho người dùng dựa trên dữ liệu hiện có"""
    print("Đang thêm bài hát yêu thích...")
    
    # Xóa tất cả bài hát yêu thích hiện có
    for user in User.objects.all():
        user.favorite_songs.clear()
    
    users = User.objects.all()
    songs = Song.objects.all()
    
    if not songs.exists():
        print("Không có bài hát trong hệ thống")
        return
    
    total_favorites = 0
    
    # Mỗi người dùng sẽ yêu thích 5-15 bài hát ngẫu nhiên
    for user in users:
        # Số lượng bài hát yêu thích
        num_favorites = min(random.randint(5, 15), songs.count())
        favorite_songs = random.sample(list(songs), num_favorites)
        
        # Thêm vào danh sách yêu thích
        for song in favorite_songs:
            user.favorite_songs.add(song)
            total_favorites += 1
    
    print(f"Đã thêm {total_favorites} lượt yêu thích bài hát cho {users.count()} người dùng")

def create_chat_messages():
    """Tạo tin nhắn giữa người dùng dựa trên dữ liệu hiện có"""
    print("Đang tạo tin nhắn chat...")
    
    # Xóa tin nhắn hiện có
    Message.objects.all().delete()
    
    users = User.objects.all()
    songs = Song.objects.all()
    
    if users.count() < 2:
        print("Cần ít nhất 2 người dùng để tạo tin nhắn")
        return
    
    # Tin nhắn mẫu
    message_templates = [
        "Chào bạn, bạn khỏe không?",
        "Bạn có nghe bài hát này chưa?",
        "Bài hát này hay lắm, nghe thử đi!",
        "Playlist của tôi có bài này, bạn nghe thử nhé",
        "Bạn thích thể loại nhạc gì?",
        "Tôi vừa tìm thấy nghệ sĩ này, rất hay!",
        "Cuối tuần này bạn nghe gì?",
        "Album mới của ca sĩ này rất tuyệt vời",
        "Bạn có playlist nào hay không?",
        "Chia sẻ với tôi bài hát yêu thích của bạn đi!"
    ]
    
    total_messages = 0
    
    # Tạo tin nhắn giữa các cặp người dùng đang theo dõi nhau
    for sender in users:
        following = sender.following.all()
        
        if not following.exists():
            continue
        
        # Chọn ngẫu nhiên một số người để nhắn tin
        num_receivers = max(1, min(3, following.count()))
        receivers = random.sample(list(following), num_receivers)
        
        for receiver in receivers:
            # Số lượng tin nhắn
            num_messages = random.randint(3, 10)
            
            # Thời gian bắt đầu (trong vòng 1 tuần trở lại)
            start_date = timezone.now() - timedelta(days=7)
            
            for i in range(num_messages):
                # Thời gian tin nhắn
                message_time = start_date + timedelta(
                    days=random.randint(0, 7),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Loại tin nhắn
                message_type = random.choice(['TEXT', 'SONG', 'TEXT', 'TEXT'])
                
                content = random.choice(message_templates)
                shared_song = None
                
                if message_type == 'SONG' and songs.exists():
                    shared_song = random.choice(songs)
                    content = f"Nghe thử bài này đi: {shared_song.title}"
                
                # Tạo tin nhắn
                Message.objects.create(
                    sender=sender,
                    receiver=receiver,
                    content=content,
                    timestamp=message_time,
                    is_read=random.choice([True, True, False]),  # 2/3 đã đọc
                    message_type=message_type,
                    shared_song=shared_song
                )
                
                total_messages += 1
    
    print(f"Đã tạo {total_messages} tin nhắn giữa người dùng")

def main():
    """Chạy tất cả các hàm tạo dữ liệu"""
    print("=" * 80)
    print("KHỞI TẠO DỮ LIỆU SOCIAL DỰA TRÊN DỮ LIỆU HIỆN CÓ")
    print("=" * 80)
    
    start_time = time.time()
    
    # Kiểm tra dữ liệu hiện có
    users_count = User.objects.count()
    songs_count = Song.objects.count()
    print(f"Dữ liệu hiện có: {users_count} người dùng, {songs_count} bài hát")
    
    if users_count < 2:
        print("Cần ít nhất 2 người dùng để tạo dữ liệu xã hội!")
        return
        
    # 1. Tạo mối quan hệ theo dõi
    create_following_relationships()
    
    # 2. Thêm bài hát yêu thích
    add_favorite_songs()
    
    # 3. Tạo tin nhắn
    create_chat_messages()
    
    # Tổng kết
    duration = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"HOÀN THÀNH TẠO DỮ LIỆU TRONG {duration:.2f} GIÂY")
    print("=" * 80)
    
    print("\nAPI để truy cập dữ liệu:")
    print("- Danh sách người đang theo dõi: GET /api/v1/accounts/social/following/")
    print("- Danh sách người theo dõi: GET /api/v1/accounts/social/followers/")
    print("- Tìm kiếm người dùng: GET /api/v1/accounts/social/search/?q=tên")
    print("- Gợi ý người dùng: GET /api/v1/accounts/social/recommendations/")
    print("- Theo dõi người dùng: POST /api/v1/accounts/social/follow/{user_id}/")
    print("- Hủy theo dõi: POST /api/v1/accounts/social/unfollow/{user_id}/")
    print("- Danh sách cuộc trò chuyện: GET /api/v1/chat/conversations/") 
    print("- Chi tiết cuộc trò chuyện: GET /api/v1/chat/conversations/{user_id}/")

if __name__ == "__main__":
    main() 