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
        
        # Lấy thông tin người nhận từ room_name (username của người nhận)
        receiver_user = await self.get_user_by_username(self.room_name)
        if not receiver_user:
            await self.close(code=4004)  # Không tìm thấy người dùng
            return

        self.receiver = receiver_user

        # Tự động tạo kết nối nếu chưa tồn tại
        await self.ensure_connection_exists(self.user, self.receiver)

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
            
            # Gửi thông báo trạng thái online (tùy chọn)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'username': self.user.username,
                    'status': 'online'
                }
            )

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'channel_layer') and hasattr(self, 'room_group_name') and self.channel_layer is not None and self.room_group_name is not None:
                # Gửi thông báo người dùng offline (tùy chọn)
                if hasattr(self, 'user') and self.user is not None and hasattr(self.user, 'username'):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'user_status',
                            'username': self.user.username,
                            'status': 'offline'
                        }
                    )
                
                # Rời room
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
        except Exception as e:
            print(f"Disconnect error: {str(e)}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Đảm bảo user đã được khởi tạo đúng
        if self.user is None:
            await self.send(text_data=json.dumps({
                'error': 'Lỗi xác thực người dùng, vui lòng kết nối lại'
            }))
            return
            
        # Xử lý các loại tin nhắn khác nhau
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            # Xử lý tin nhắn thông thường
            await self.handle_chat_message(data)
        elif message_type == 'typing':
            # Xử lý trạng thái đang nhập
            await self.handle_typing_indicator(data)
        elif message_type == 'read':
            # Xử lý đánh dấu đã đọc
            await self.handle_read_receipt(data)
        else:
            # Loại tin nhắn không được hỗ trợ
            await self.send(text_data=json.dumps({
                'error': f'Unsupported message type: {message_type}'
            }))

    async def handle_chat_message(self, data):
        message = data['message']
        username = data['username']
        room = data.get('room', self.room_name)

        # Kiểm tra user và receiver đã được khởi tạo đúng
        if self.user is None or self.receiver is None:
            await self.send(text_data=json.dumps({
                'error': 'Lỗi xác thực người dùng, vui lòng kết nối lại'
            }))
            return

        # Lưu tin nhắn vào cơ sở dữ liệu
        message_obj = await self.save_message(username, room, message)

        # Send message to room group
        if hasattr(self, 'channel_layer') and self.channel_layer is not None and self.room_group_name is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'timestamp': message_obj.get('timestamp', timezone.now().isoformat()),
                    'message_id': message_obj.get('id')
                }
            )

    async def handle_typing_indicator(self, data):
        is_typing = data.get('is_typing', False)
        
        # Đảm bảo user đã được khởi tạo đúng
        if self.user is None or not hasattr(self.user, 'username'):
            return
            
        # Gửi trạng thái đang nhập đến tất cả người dùng trong phòng
        if hasattr(self, 'channel_layer') and self.channel_layer is not None and self.room_group_name is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'username': self.user.username,
                    'is_typing': is_typing
                }
            )

    async def handle_read_receipt(self, data):
        # Đảm bảo user và receiver đã được khởi tạo đúng
        if self.user is None or self.receiver is None or not hasattr(self.user, 'username'):
            return
            
        # Đánh dấu tất cả tin nhắn từ người nhận là đã đọc
        await self.mark_messages_as_read()
        
        # Thông báo cho người gửi rằng tin nhắn đã được đọc
        if hasattr(self, 'channel_layer') and self.channel_layer is not None and self.room_group_name is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'username': self.user.username,
                    'timestamp': timezone.now().isoformat()
                }
            )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        timestamp = event.get('timestamp', timezone.now().isoformat())
        message_id = event.get('message_id')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message,
            'username': username,
            'timestamp': timestamp,
            'message_id': message_id
        }))

    async def typing_indicator(self, event):
        # Gửi trạng thái đang nhập cho client
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def user_status(self, event):
        # Gửi trạng thái người dùng (online/offline) cho client
        await self.send(text_data=json.dumps({
            'type': 'status',
            'username': event['username'],
            'status': event['status']
        }))
        
    async def read_receipt(self, event):
        # Gửi xác nhận đã đọc cho client
        await self.send(text_data=json.dumps({
            'type': 'read',
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, username, room, message):
        # Lưu tin nhắn vào database
        try:
            sender = self.user
            receiver = self.receiver
            message_obj = Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=message,
                is_read=False
            )
            return {
                'id': message_obj.id,
                'timestamp': message_obj.created_at.isoformat()
            }
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return {}

    @database_sync_to_async
    def get_user_by_username(self, username):
        """Lấy thông tin người dùng từ username"""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def ensure_connection_exists(self, user1, user2):
        """Tự động tạo hoặc cập nhật kết nối giữa hai người dùng nếu chưa tồn tại"""
        # Kiểm tra xem kết nối đã tồn tại chưa
        connection = UserConnection.get_connection(user1, user2)
        
        if connection:
            # Nếu kết nối ở trạng thái PENDING hoặc DECLINED, cập nhật thành ACCEPTED
            if connection.status in ['PENDING', 'DECLINED']:
                connection.status = 'ACCEPTED'
                connection.save(update_fields=['status'])
        else:
            # Tạo kết nối mới với trạng thái ACCEPTED
            if user1.id < user2.id:
                requester, receiver = user1, user2
            else:
                requester, receiver = user2, user1
                
            UserConnection.objects.create(
                requester=requester,
                receiver=receiver,
                status='ACCEPTED'
            )
        
        return True
        
    @database_sync_to_async
    def mark_messages_as_read(self):
        """Đánh dấu tất cả tin nhắn từ receiver gửi đến user là đã đọc"""
        try:
            updated = Message.objects.filter(
                sender=self.receiver,
                receiver=self.user,
                is_read=False
            ).update(is_read=True)
            
            return updated
        except Exception as e:
            print(f"Error marking messages as read: {str(e)}")
            return 0