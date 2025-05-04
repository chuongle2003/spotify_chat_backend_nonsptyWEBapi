import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Message, ChatRestriction

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None

    async def connect(self):
        self.user = self.scope["user"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Kiểm tra xem người dùng có bị hạn chế không
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        is_restricted = await self.check_user_restriction(self.user)
        if is_restricted:
            await self.close(code=4000)
            return

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
        room = data['room']

        # Kiểm tra lại quyền gửi tin nhắn
        is_restricted = await self.check_user_restriction(self.user)
        if is_restricted:
            await self.send(text_data=json.dumps({
                'error': 'Tính năng chat của bạn đã bị hạn chế bởi quản trị viên'
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
            receiver = User.objects.get(username=room)
            Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=message,
                is_read=False
            )
        except User.DoesNotExist:
            # Xử lý khi không tìm thấy người nhận
            pass

    @database_sync_to_async
    def check_user_restriction(self, user):
        """Kiểm tra xem người dùng có bị hạn chế chat không"""
        
        # Admin luôn được phép chat
        if user.is_admin:
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