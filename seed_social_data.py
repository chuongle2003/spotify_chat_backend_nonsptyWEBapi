#!/usr/bin/env python
"""
Script để tạo dữ liệu mẫu cho các API social (following, recommendations)
Tạo mối quan hệ giữa người dùng, bài hát yêu thích, và các mối liên kết xã hội
"""

import os
import sys
import django
import random
from django.db.models import Count
from datetime import timedelta

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from music.models import Song, Genre, Artist, Playlist
from django.utils import timezone
from chat.models import Message

User = get_user_model()

def create_following_relationships():
    """Tạo mối quan hệ theo dõi giữa người dùng"""
    print("Đang tạo mối quan hệ theo dõi...")
    
    users = User.objects.all()
    
    if users.count() < 5:
        print("Không đủ người dùng để tạo mối quan hệ theo dõi (cần ít nhất 5)")
        return
    
    # Mỗi người dùng sẽ theo dõi 30-70% người dùng khác ngẫu nhiên
    for user in users:
        # Loại bỏ người dùng hiện tại
        other_users = users.exclude(id=user.id)
        
        # Tính số lượng người dùng sẽ theo dõi
        num_to_follow = random.randint(int(other_users.count() * 0.3), int(other_users.count() * 0.7))
        users_to_follow = random.sample(list(other_users), num_to_follow)
        
        # Theo dõi người dùng
        for user_to_follow in users_to_follow:
            user.following.add(user_to_follow)
        
        print(f"Người dùng {user.username} đang theo dõi {num_to_follow} người")

def create_favorite_songs():
    """Thêm bài hát yêu thích cho người dùng"""
    print("Đang thêm bài hát yêu thích...")
    
    users = User.objects.all()
    songs = Song.objects.all()
    
    if songs.count() < 10:
        print("Không đủ bài hát để tạo yêu thích (cần ít nhất 10)")
        return
    
    # Mỗi người dùng sẽ yêu thích 10-30 bài hát ngẫu nhiên
    for user in users:
        # Xóa bài hát yêu thích cũ (nếu có)
        user.favorite_songs.clear()
        
        # Số lượng bài hát yêu thích
        num_favorites = min(random.randint(10, 30), songs.count())
        favorite_songs = random.sample(list(songs), num_favorites)
        
        # Thêm vào danh sách yêu thích
        for song in favorite_songs:
            user.favorite_songs.add(song)
        
        print(f"Người dùng {user.username} có {num_favorites} bài hát yêu thích")

def create_chat_messages():
    """Tạo tin nhắn giữa người dùng"""
    print("Đang tạo tin nhắn chat...")
    
    users = User.objects.all()
    songs = Song.objects.all()
    
    if users.count() < 2:
        print("Không đủ người dùng để tạo tin nhắn (cần ít nhất 2)")
        return
        
    if songs.count() < 1:
        print("Không có bài hát để chia sẻ trong tin nhắn")
        return
    
    # Xóa tin nhắn cũ
    Message.objects.all().delete()
    
    # Tạo tin nhắn giữa các cặp người dùng đang theo dõi nhau
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
    
    # Mỗi người dùng sẽ nhắn tin với 40-80% người mà họ theo dõi
    for sender in users:
        following = sender.following.all()
        
        if not following.exists():
            continue
            
        # Số người nhận tin nhắn
        num_receivers = random.randint(int(following.count() * 0.4), int(following.count() * 0.8))
        receivers = random.sample(list(following), min(num_receivers, following.count()))
        
        for receiver in receivers:
            # Số lượng tin nhắn
            num_messages = random.randint(3, 15)
            
            # Thời gian bắt đầu (trong vòng 1 tháng trở lại)
            start_date = timezone.now() - timedelta(days=30)
            
            for i in range(num_messages):
                # Thời gian tin nhắn
                message_time = start_date + timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Loại tin nhắn
                message_type = random.choice(['TEXT', 'SONG', 'TEXT', 'TEXT', 'TEXT'])
                
                content = random.choice(message_templates)
                shared_song = None
                
                if message_type == 'SONG':
                    shared_song = random.choice(songs)
                
                # Tạo tin nhắn
                Message.objects.create(
                    sender=sender,
                    receiver=receiver,
                    content=content,
                    timestamp=message_time,
                    is_read=random.choice([True, True, True, False]),  # 75% đã đọc
                    message_type=message_type,
                    shared_song=shared_song
                )
                
                total_messages += 1
                
    print(f"Đã tạo tổng cộng {total_messages} tin nhắn")

def run_all():
    """Chạy tất cả các hàm tạo dữ liệu"""
    print("Bắt đầu tạo dữ liệu mẫu cho các API social...")
    
    create_following_relationships()
    create_favorite_songs()
    create_chat_messages()
    
    print("Hoàn thành tạo dữ liệu mẫu!")

if __name__ == "__main__":
    run_all() 