"""
WebSocket URL routing for AI Assistant
"""
from django.urls import re_path
from . import consumers
 
websocket_urlpatterns = [
    re_path(r'ws/ai/chat/(?P<conversation_id>\w+)/$', consumers.AIChatConsumer.as_asgi()),
    re_path(r'ws/ai/chat/$', consumers.AIChatConsumer.as_asgi()),
] 