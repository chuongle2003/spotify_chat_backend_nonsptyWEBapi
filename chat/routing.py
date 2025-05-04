from django.urls import re_path
from . import consumers
from .middleware import ChatRestrictionMiddleware

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", ChatRestrictionMiddleware(consumers.ChatConsumer.as_asgi())),
] 