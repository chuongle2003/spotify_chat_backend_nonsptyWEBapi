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

# Lấy ứng dụng ASGI Django trước
django_asgi_app = get_asgi_application()

# Import các URL patterns sau khi đã khởi tạo Django settings
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from ai_assistant.routing import websocket_urlpatterns as ai_websocket_urlpatterns

# Combine websocket patterns from different apps
all_websocket_urlpatterns = chat_websocket_urlpatterns + ai_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            all_websocket_urlpatterns
        )
    ),
})
