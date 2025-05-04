from django.urls import path
from chat import views

urlpatterns = [
    # API lịch sử và quản lý tin nhắn
    path('api/chat/history/<str:username>/', views.MessageListView.as_view(), name='message_history'),
    path('api/chat/unread/count/', views.UnreadCountView.as_view(), name='unread_count'),
    path('api/chat/mark-read/<str:username>/', views.MarkReadView.as_view(), name='mark_read'),
    
    # API hạn chế chat (dành cho admin)
    path('api/chat/restrictions/', views.ChatRestrictionListView.as_view(), name='chat_restrictions'),
    path('api/chat/restrict/<int:user_id>/', views.RestrictUserView.as_view(), name='restrict_user'),
    path('api/chat/unrestrict/<int:user_id>/', views.UnrestrictUserView.as_view(), name='unrestrict_user'),
] 