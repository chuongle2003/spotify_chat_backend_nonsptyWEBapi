from django.urls import path
from . import views
from . import consumers

urlpatterns = [
    # Chat endpoints
    path('messages/', views.MessageListView.as_view(), name='message-list'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message-detail'),
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:user_id>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
]

# WebSocket URLs - được xử lý riêng bởi routing.py
websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
] 