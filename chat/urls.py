from django.urls import path
from . import views
from . import consumers
from .views import (
    MessageListView, MessageCreateView, MessageDetailView, 
    ConversationListView, ConversationDetailView, StartConversationView,
    ReportMessageView, AdminMessageListView, AdminMessageDetailView,
    AdminMessageReportListView, AdminMessageReportDetailView,
    AdminChatRestrictionListView, AdminChatRestrictionDetailView, AdminUserChatStatsView,
    UserSearchView, ChatSuggestionView, MessageHistoryView
)

urlpatterns = [
    # API cho người dùng thông thường
    path('messages/', MessageListView.as_view(), name='message-list'),
    path('messages/create/', MessageCreateView.as_view(), name='message-create'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('messages/history/', MessageHistoryView.as_view(), name='message-history'),
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/messages/', ConversationDetailView.as_view(), name='conversation-messages'),
    path('conversations/start/', StartConversationView.as_view(), name='start-conversation'),
    path('report-message/', ReportMessageView.as_view(), name='report-message'),
    
    # API tìm kiếm và gợi ý người dùng
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('users/suggestions/', ChatSuggestionView.as_view(), name='chat-suggestions'),
    
    # API cho admin quản lý
    path('admin/messages/', AdminMessageListView.as_view(), name='admin-message-list'),
    path('admin/messages/<int:pk>/', AdminMessageDetailView.as_view(), name='admin-message-detail'),
    path('admin/reports/', AdminMessageReportListView.as_view(), name='admin-report-list'),
    path('admin/reports/<int:pk>/', AdminMessageReportDetailView.as_view(), name='admin-report-detail'),
    path('admin/reports/statistics/', views.AdminMessageReportStatsView.as_view(), name='admin-report-stats'),
    path('admin/reports/pending/', views.AdminPendingReportsView.as_view(), name='admin-pending-reports'),
    path('admin/restrictions/', AdminChatRestrictionListView.as_view(), name='admin-restriction-list'),
    path('admin/restrictions/<int:pk>/', AdminChatRestrictionDetailView.as_view(), name='admin-restriction-detail'),
    path('admin/stats/', AdminUserChatStatsView.as_view(), name='admin-chat-stats'),
    path('admin/stats/<int:user_id>/', AdminUserChatStatsView.as_view(), name='admin-user-chat-stats'),
]

# WebSocket URLs - được xử lý riêng bởi routing.py
# Đã được cập nhật trong routing.py
websocket_urlpatterns = [] 