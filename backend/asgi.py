"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

# Đặt biến môi trường trước khi import các module khác
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from chat.middleware import get_user_from_token
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs

# Lấy ứng dụng ASGI Django trước
django_asgi_app = get_asgi_application()

# Tạo middleware JWT
class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Lấy token từ query param hoặc headers
        query_params = parse_qs(scope["query_string"].decode())
        token = None
        
        if b'token' in query_params:
            token = query_params[b'token'][0].decode()
        
        if not token and 'headers' in scope:
            for name, value in scope.get('headers', []):
                if name == b'authorization':
                    token_name, token = value.decode().split()
                    if token_name.lower() == 'bearer':
                        break
        
        if token:
            # Lấy người dùng từ token
            user = await database_sync_to_async(get_user_from_token)(token)
            if user:
                scope['user'] = user
        
        return await super().__call__(scope, receive, send)

# Import các URL patterns sau khi đã khởi tạo Django settings
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from ai_assistant.routing import websocket_urlpatterns as ai_websocket_urlpatterns

# Combine websocket patterns from different apps
all_websocket_urlpatterns = chat_websocket_urlpatterns + ai_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                all_websocket_urlpatterns
            )
        )
    ),
})
