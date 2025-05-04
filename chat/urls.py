from django.urls import path
from . import views
from . import consumers
from .views import (
    MessageListView, MessageDetailView, ConversationListView, ConversationDetailView,
    ReportMessageView, AdminMessageListView, AdminMessageDetailView,
    AdminMessageReportListView, AdminMessageReportDetailView,
    AdminChatRestrictionListView, AdminChatRestrictionDetailView, AdminUserChatStatsView
)

urlpatterns = [
    # API cho người dùng thông thường
    path('messages/', MessageListView.as_view(), name='message-list'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:user_id>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('report-message/', ReportMessageView.as_view(), name='report-message'),
    
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
websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
] 