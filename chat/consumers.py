import json
import logging
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
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None
        self.receiver = None
        self.channel_layer = None

    async def connect(self):
        try:
            self.user = self.scope["user"]
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.channel_layer = get_channel_layer()

            # Kiểm tra xác thực
            if not self.user.is_authenticated:
                await self.send_error("UNAUTHORIZED", "Người dùng chưa đăng nhập")
                await self.close(code=4001)
                return
            
            # Lấy thông tin người nhận
            receiver_user = await self.get_user_by_username(self.room_name)
            if not receiver_user:
                await self.send_error("USER_NOT_FOUND", f"Không tìm thấy người dùng {self.room_name}")
                await self.close(code=4004)
                return

            self.receiver = receiver_user

            # Kiểm tra kết nối giữa hai người dùng
            is_connected = await self.check_user_connection(self.user, self.receiver)
            if not is_connected:
                await self.send_error("NOT_CONNECTED", "Bạn cần kết nối với người dùng này trước khi chat")
                await self.close(code=4005)
                return

            # Tạo tên nhóm chat
            user_ids = sorted([str(self.user.id), str(self.receiver.id)])
            self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

            # Tham gia nhóm
            if self.channel_layer is not None:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                
                # Gửi thông báo kết nối thành công
                await self.send_success("CONNECTED", {
                    "room_name": self.room_group_name,
                    "receiver": {
                        "id": self.receiver.id,
                        "username": self.receiver.username
                    }
                })
            else:
                await self.send_error("CHANNEL_ERROR", "Lỗi kết nối channel")
                await self.close(code=4006)

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.send_error("CONNECTION_ERROR", "Lỗi kết nối")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        try:
            if self.channel_layer is not None and self.room_group_name is not None:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message')
            message_type = data.get('type', 'message')

            if not self.user or not self.receiver:
                await self.send_error("INVALID_STATE", "Kết nối không hợp lệ")
                return

            if self.channel_layer is None:
                await self.send_error("CHANNEL_ERROR", "Lỗi kết nối channel")
                return

            if message_type == 'message':
                if not message:
                    await self.send_error("INVALID_MESSAGE", "Tin nhắn không được để trống")
                    return

                # Lưu tin nhắn
                saved_message = await self.save_message(message)
                if not saved_message:
                    await self.send_error("SAVE_ERROR", "Không thể lưu tin nhắn")
                    return

                # Gửi tin nhắn đến nhóm
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.user.id,
                        'sender_username': self.user.username,
                        'timestamp': timezone.now().isoformat(),
                        'message_id': saved_message.id
                    }
                )

            elif message_type == 'typing':
                # Gửi trạng thái đang gõ
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'is_typing': data.get('is_typing', True)
                    }
                )

        except json.JSONDecodeError:
            await self.send_error("INVALID_JSON", "Dữ liệu không hợp lệ")
        except Exception as e:
            logger.error(f"Receive error: {str(e)}")
            await self.send_error("INTERNAL_ERROR", "Lỗi hệ thống")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def send_error(self, code, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'code': code,
            'message': message
        }))

    async def send_success(self, code, data):
        await self.send(text_data=json.dumps({
            'type': 'success',
            'code': code,
            'data': data
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
            logger.error(f"Error saving message: {str(e)}")
            return None
    
    @database_sync_to_async
    def get_user_by_username(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def check_user_connection(self, user1, user2):
        try:
            return UserConnection.objects.filter(
                (Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)),
                is_accepted=True
            ).exists()
        except Exception as e:
            logger.error(f"Error checking user connection: {str(e)}")
            return False