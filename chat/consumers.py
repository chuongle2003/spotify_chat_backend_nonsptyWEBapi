import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Message, ChatRestriction

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    ERROR_CODES = {
        'UNAUTHORIZED': 4001,
        'USER_NOT_FOUND': 4004,
        'RESTRICTED': 4005,
        'INVALID_MESSAGE': 4006,
        'INTERNAL_ERROR': 4007
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None
        self.receiver = None

    async def connect(self):
        self.user = self.scope["user"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        if not self.user.is_authenticated:
            await self.send_error('UNAUTHORIZED', 'Vui lòng đăng nhập để sử dụng tính năng chat')
            await self.close(code=self.ERROR_CODES['UNAUTHORIZED'])
            return

        self.receiver = await self.get_user_by_username(self.room_name)
        if not self.receiver:
            await self.send_error('USER_NOT_FOUND', f'Không tìm thấy người dùng {self.room_name}')
            await self.close(code=self.ERROR_CODES['USER_NOT_FOUND'])
            return

        if await self.check_user_restriction(self.user):
            await self.send_error('RESTRICTED', 'Tính năng chat của bạn đã bị hạn chế')
            await self.close(code=self.ERROR_CODES['RESTRICTED'])
            return

        user_ids = sorted([str(self.user.id), str(self.receiver.id)])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_success('CONNECTED', 'Kết nối WebSocket thành công')

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message', '').strip()

            if not message:
                await self.send_error('INVALID_MESSAGE', 'Tin nhắn không hợp lệ')
                return

            saved = await self.save_message(message)
            if saved:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': self.user.username,
                        'timestamp': timezone.now().isoformat()
                    }
                )

        except json.JSONDecodeError:
            await self.send_error('INVALID_MESSAGE', 'Định dạng tin nhắn không hợp lệ')
        except Exception as e:
            await self.send_error('INTERNAL_ERROR', f'Lỗi hệ thống: {str(e)}')

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, message):
        try:
            return Message.objects.create(
                sender=self.user,
                receiver=self.receiver,
                content=message,
                is_read=False
            )
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    @database_sync_to_async
    def check_user_restriction(self, user):
        return False  # Tùy chỉnh theo logic hạn chế thật nếu cần

    @database_sync_to_async
    def get_user_by_username(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    async def send_error(self, code, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'code': code,
            'message': message
        }))

    async def send_success(self, code, message):
        await self.send(text_data=json.dumps({
            'type': 'success',
            'code': code,
            'message': message
        }))
