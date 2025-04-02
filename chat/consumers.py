import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None

    async def connect(self):
        try:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'

            # Tham gia room
            if self.channel_layer:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
            else:
                print("Channel layer is not available")
                await self.close()
        except Exception as e:
            print(f"Connect error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if self.channel_layer and self.room_group_name:
                # Rời room
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
        except Exception as e:
            print(f"Disconnect error: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data['message']
            
            if self.channel_layer and self.room_group_name:
                # Gửi tin nhắn đến room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message
                    }
                )
        except Exception as e:
            print(f"Receive error: {str(e)}")

    async def chat_message(self, event):
        try:
            message = event['message']
            # Gửi tin nhắn đến WebSocket
            await self.send(text_data=json.dumps({
                'message': message
            }))
        except Exception as e:
            print(f"Chat message error: {str(e)}")