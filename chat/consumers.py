import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import Message, ChatRestriction, Conversation

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    ERROR_CODES = {
        'UNAUTHORIZED': 4001,
        'USER_NOT_FOUND': 4004,
        'CONVERSATION_NOT_FOUND': 4005,
        'RESTRICTED': 4006,
        'INVALID_MESSAGE': 4007,
        'INTERNAL_ERROR': 4008
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_id = None
        self.conversation = None
        self.room_group_name = None
        self.user = None

    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']

        if not self.user.is_authenticated:
            await self.send_error('UNAUTHORIZED', 'Vui lòng đăng nhập để sử dụng tính năng chat')
            await self.close(code=self.ERROR_CODES['UNAUTHORIZED'])
            return

        # Kiểm tra xem cuộc trò chuyện có tồn tại không
        self.conversation = await self.get_conversation(self.conversation_id)
        if not self.conversation:
            await self.send_error('CONVERSATION_NOT_FOUND', f'Không tìm thấy cuộc trò chuyện ID: {self.conversation_id}')
            await self.close(code=self.ERROR_CODES['CONVERSATION_NOT_FOUND'])
            return

        # Kiểm tra xem người dùng có tham gia vào cuộc trò chuyện không
        if not await self.check_user_in_conversation(self.user, self.conversation):
            await self.send_error('UNAUTHORIZED', 'Bạn không phải là thành viên của cuộc trò chuyện này')
            await self.close(code=self.ERROR_CODES['UNAUTHORIZED'])
            return

        # Kiểm tra xem người dùng có bị hạn chế không
        if await self.check_user_restriction(self.user):
            await self.send_error('RESTRICTED', 'Tính năng chat của bạn đã bị hạn chế')
            await self.close(code=self.ERROR_CODES['RESTRICTED'])
            return

        self.room_group_name = f'chat_{self.conversation_id}'

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
            message_type = data.get('message_type', 'TEXT')
            
            # Kiểm tra loại tin nhắn
            if message_type not in [choice[0] for choice in Message.MESSAGE_TYPES]:
                message_type = 'TEXT'
                
            # Có thể mở rộng để xử lý các loại tin nhắn khác như song_id, playlist_id, v.v.
            song_id = data.get('song_id')
            playlist_id = data.get('playlist_id')
            
            if not message and message_type == 'TEXT':
                await self.send_error('INVALID_MESSAGE', 'Tin nhắn không hợp lệ')
                return

            # Lấy người nhận từ cuộc trò chuyện (người còn lại ngoài người gửi)
            receiver = await self.get_other_participant(self.conversation, self.user)
            
            saved_message = await self.save_message(message, message_type, receiver, song_id, playlist_id)
            if saved_message:
                # Cập nhật thời gian của conversation
                await self.update_conversation_time(self.conversation)
                
                # Chuẩn bị dữ liệu cho tin nhắn
                message_data = {
                    'id': saved_message.id,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'receiver_id': receiver.id if receiver else None,
                    'message': message,
                    'message_type': message_type,
                    'timestamp': timezone.now().isoformat(),
                    'is_read': False
                }
                
                # Thêm dữ liệu cho các loại tin nhắn đặc biệt
                if song_id and message_type == 'SONG':
                    message_data['song_id'] = song_id
                if playlist_id and message_type == 'PLAYLIST':
                    message_data['playlist_id'] = playlist_id
                
                # Gửi tin nhắn cho tất cả người dùng trong group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message_data': message_data
                    }
                )

        except json.JSONDecodeError:
            await self.send_error('INVALID_MESSAGE', 'Định dạng tin nhắn không hợp lệ')
        except Exception as e:
            await self.send_error('INTERNAL_ERROR', f'Lỗi hệ thống: {str(e)}')

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message_data']
        }))

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        try:
            return Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def check_user_in_conversation(self, user, conversation):
        return conversation.participants.filter(id=user.id).exists()

    @database_sync_to_async
    def get_other_participant(self, conversation, user):
        return conversation.get_other_participant(user)

    @database_sync_to_async
    def save_message(self, content, message_type, receiver, song_id=None, playlist_id=None):
        try:
            message_data = {
                'sender': self.user,
                'receiver': receiver,
                'conversation': self.conversation,
                'content': content,
                'is_read': False,
                'message_type': message_type
            }
            
            # Thêm dữ liệu cho các loại tin nhắn đặc biệt
            if song_id and message_type == 'SONG':
                from music.models import Song
                try:
                    song = Song.objects.get(id=song_id)
                    message_data['shared_song'] = song
                except Song.DoesNotExist:
                    pass
                    
            if playlist_id and message_type == 'PLAYLIST':
                from music.models import Playlist
                try:
                    playlist = Playlist.objects.get(id=playlist_id)
                    message_data['shared_playlist'] = playlist
                except Playlist.DoesNotExist:
                    pass
                    
            return Message.objects.create(**message_data)
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    @database_sync_to_async
    def update_conversation_time(self, conversation):
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

    @database_sync_to_async
    def check_user_restriction(self, user):
        """Kiểm tra xem người dùng có bị hạn chế chat không"""
        try:
            active_restrictions = ChatRestriction.objects.filter(
                user=user, 
                is_active=True
            )
            
            for restriction in active_restrictions:
                # Nếu là hạn chế vĩnh viễn hoặc chưa hết hạn
                if restriction.restriction_type == 'PERMANENT' or not restriction.is_expired:
                    return True
                    
            return False
        except Exception:
            return False

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
