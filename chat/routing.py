from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Đường dẫn hỗ trợ token query parameter (token=<JWT_TOKEN>)
    re_path(r'ws/chat/(?P<conversation_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
] 