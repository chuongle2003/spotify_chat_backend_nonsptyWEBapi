import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from .models import Message, ChatRestriction
from accounts.models import UserConnection

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None
        self.receiver = None

    async def connect(self):
        self.user = self.scope["user"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        # Kiểm tra xem người dùng có đăng nhập không
        if not self.user.is_authenticated:
            print("Người dùng chưa đăng nhập, đóng kết nối WebSocket")
            await self.close(code=4001)
            return
        
        # Lấy thông tin người nhận từ room_name (thường là username)
        receiver_user = await self.get_user_by_username(self.room_name)
        if not receiver_user:
            print(f"Không tìm thấy người dùng với username {self.room_name}")
            await self.close(code=4004)  # Không tìm thấy người dùng
            return

        self.receiver = receiver_user

        # In thông tin debug
        print(f"WebSocket kết nối: {self.user.username} -> {self.receiver.username}")

        # Tạo tên nhóm duy nhất cho cuộc trò chuyện giữa hai người
        # Sắp xếp ID để đảm bảo tên nhóm giống nhau bất kể ai kết nối trước
        user_ids = sorted([str(self.user.id), str(self.receiver.id)])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        # Lấy channel_layer
        self.channel_layer = get_channel_layer()

        # Join room group
        if self.channel_layer is not None and self.room_group_name is not None:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            print(f"Đã tham gia nhóm: {self.room_group_name}")
            await self.accept()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'channel_layer') and hasattr(self, 'room_group_name') and self.channel_layer is not None and self.room_group_name is not None:
                # Rời room
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
        except Exception as e:
            print(f"Disconnect error: {str(e)}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        room = data.get('room', self.room_name)

        # Đảm bảo user đã được khởi tạo đúng
        if self.user is None:
            await self.send(text_data=json.dumps({
                'error': 'Lỗi xác thực người dùng, vui lòng kết nối lại'
            }))
            return

        # Lưu tin nhắn vào cơ sở dữ liệu
        await self.save_message(username, room, message)

        # Send message to room group
        if hasattr(self, 'channel_layer') and self.channel_layer is not None and self.room_group_name is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                }
            )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))

    @database_sync_to_async
    def save_message(self, username, room, message):
        # Lưu tin nhắn vào database
        try:
            sender = self.user
            receiver = self.receiver
            Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=message,
                is_read=False
            )
        except Exception as e:
            print(f"Error saving message: {str(e)}")

    @database_sync_to_async
    def check_user_restriction(self, user):
        """Kiểm tra xem người dùng có bị hạn chế chat không"""
        # Luôn trả về False để bỏ chức năng chặn người dùng chat
        return False
    
    @database_sync_to_async
    def get_user_by_username(self, username):
        """Lấy thông tin người dùng từ username"""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def check_user_connection(self, user1, user2):
        """Kiểm tra xem hai người dùng có kết nối với nhau không"""
        # Luôn trả về True để bỏ chức năng kiểm tra kết nối
        return True