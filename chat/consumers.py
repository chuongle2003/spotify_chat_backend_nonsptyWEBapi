import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message

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

        if not self.user.is_authenticated:
            await self.send_json({
                'event': 'ERROR',
                'code': 'AUTH_REQUIRED',
                'error': 'Người dùng chưa đăng nhập.'
            })
            await self.close(code=4001)
            return

        receiver_user = await self.get_user_by_username(self.room_name)
        if not receiver_user:
            await self.send_json({
                'event': 'ERROR',
                'code': 'USER_NOT_FOUND',
                'error': f'Không tìm thấy người dùng: {self.room_name}'
            })
            await self.close(code=4004)
            return

        if self.user == receiver_user:
            await self.send_json({
                'event': 'ERROR',
                'code': 'SELF_CHAT_NOT_ALLOWED',
                'error': 'Không thể tự chat với chính mình.'
            })
            await self.close(code=4005)
            return

        self.receiver = receiver_user
        user_ids = sorted([str(self.user.id), str(self.receiver.id)])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'
        self.channel_layer = get_channel_layer()

        if self.channel_layer:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
        await self.accept()
        await self.send_json({
            'event': 'CONNECTED',
            'room': self.room_group_name
        })

    async def disconnect(self, close_code):
        if self.channel_layer and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message', '').strip()

            if not message:
                await self.send_json({
                    'event': 'ERROR',
                    'code': 'MESSAGE_EMPTY',
                    'error': 'Tin nhắn không được để trống.'
                })
                return

            saved_message = await self.save_message(message)

            if saved_message:
                if self.channel_layer:
                    username = self.user.username if self.user else "unknown"
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': message,
                            'username': username,
                            'timestamp': saved_message.timestamp.isoformat(),
                            'message_id': saved_message.id,
                        }
                    )
                await self.send_json({
                    'event': 'MESSAGE_ACK',
                    'message_id': saved_message.id,
                    'timestamp': saved_message.timestamp.isoformat(),
                    'message': message,
                    'is_sender': True
                })

        except Exception as e:
            await self.send_json({
                'event': 'ERROR',
                'code': 'SERVER_ERROR',
                'error': str(e)
            })

    async def chat_message(self, event):
        is_sender = event['username'] == self.user.username if self.user else False
        await self.send_json({
            'event': 'MESSAGE_RECEIVED',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'is_sender': is_sender
        })

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
    def get_user_by_username(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
