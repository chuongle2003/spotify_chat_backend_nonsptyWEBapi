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
            await self.close(code=4001)
            return
        
        # Kiểm tra xem người dùng có bị hạn chế không
        is_restricted = await self.check_user_restriction(self.user)
        if is_restricted:
            await self.close(code=4000)
            return

        # Lấy thông tin người nhận từ room_name (thường là username)
        receiver_user = await self.get_user_by_username(self.room_name)
        if not receiver_user:
            await self.close(code=4004)  # Không tìm thấy người dùng
            return

        self.receiver = receiver_user

        # Kiểm tra quyền admin trước
        is_admin = getattr(self.user, 'is_admin', False) 
        
        # Kiểm tra xem hai người dùng có kết nối với nhau không
        can_chat = await self.check_user_connection(self.user, self.receiver)
        if not can_chat and not is_admin:  # Admin luôn có thể chat
            await self.close(code=4002)  # Chưa kết nối
            return

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

        # Kiểm tra lại quyền gửi tin nhắn
        is_restricted = await self.check_user_restriction(self.user)
        if is_restricted:
            await self.send(text_data=json.dumps({
                'error': 'Tính năng chat của bạn đã bị hạn chế bởi quản trị viên'
            }))
            return

        # Kiểm tra lại kết nối
        can_chat = await self.check_user_connection(self.user, self.receiver)
        # Kiểm tra quyền admin trước khi sử dụng
        is_admin = getattr(self.user, 'is_admin', False)
        if not can_chat and not is_admin:
            await self.send(text_data=json.dumps({
                'error': 'Bạn không thể gửi tin nhắn cho người này vì chưa kết nối'
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
        
        # Admin luôn được phép chat
        if getattr(user, 'is_admin', False):
            return False
            
        # Kiểm tra các hạn chế đang hoạt động
        active_restrictions = ChatRestriction.objects.filter(
            user=user,
            is_active=True
        )
        
        now = timezone.now()
        for restriction in active_restrictions:
            # Nếu là hạn chế vĩnh viễn hoặc chưa hết hạn
            if restriction.restriction_type == 'PERMANENT' or (restriction.expires_at and restriction.expires_at > now):
                return True
                
            # Nếu đã hết hạn, cập nhật trạng thái
            if restriction.expires_at and restriction.expires_at <= now:
                restriction.is_active = False
                restriction.save(update_fields=['is_active'])
                
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
        return UserConnection.are_connected(user1, user2)