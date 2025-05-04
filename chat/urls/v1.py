from django.urls import path
from rest_framework.routers import DefaultRouter
from chat import views

app_name = 'chat_v1'

# Sử dụng router cho ViewSets nếu có
router = DefaultRouter()

urlpatterns = [
    # Lấy tin nhắn và lịch sử chat
    path('messages/<str:username>/', views.MessageListView.as_view(), name='message-list'),
    path('messages/unread/count/', views.UnreadCountView.as_view(), name='unread-count'),
    path('messages/mark-read/<str:username>/', views.MarkReadView.as_view(), name='mark-read'),
    
    # Lấy cuộc trò chuyện
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/recent/', views.RecentConversationsView.as_view(), name='recent-conversations'),
    
    # Hạn chế chat (admin)
    path('restrictions/', views.ChatRestrictionListView.as_view(), name='restriction-list'),
    path('restrictions/<int:pk>/', views.ChatRestrictionDetailView.as_view(), name='restriction-detail'),
    path('users/<int:user_id>/restrict/', views.RestrictUserView.as_view(), name='restrict-user'),
    path('users/<int:user_id>/unrestrict/', views.UnrestrictUserView.as_view(), name='unrestrict-user'),
]

# Thêm các URL từ router
urlpatterns += router.urls 