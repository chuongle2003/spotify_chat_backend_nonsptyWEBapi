from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Max, F, ExpressionWrapper, DateTimeField
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Message, MessageReport, ChatRestriction
from .serializers import (
    MessageSerializer, ConversationSerializer, AdminMessageSerializer,
    MessageReportSerializer, MessageReportCreateSerializer, MessageReportUpdateSerializer,
    ChatRestrictionSerializer, ChatRestrictionCreateSerializer
)
from .permissions import IsAdminUser, IsMessageParticipant, IsReporter, IsNotRestricted

User = get_user_model()

# Create your views here.

# API cho người dùng thông thường
class MessageListView(generics.ListAPIView):
    """API để lấy lịch sử tin nhắn với một người dùng cụ thể"""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        username = self.kwargs.get('username')
        other_user = get_object_or_404(User, username=username)
        
        # Lấy tất cả tin nhắn giữa hai người dùng
        return Message.objects.filter(
            (Q(sender=self.request.user) & Q(receiver=other_user)) | 
            (Q(sender=other_user) & Q(receiver=self.request.user))
        ).order_by('-created_at')

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsMessageParticipant]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        )

class ConversationListView(APIView):
    """API để lấy danh sách các cuộc trò chuyện"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Lấy danh sách người dùng đã từng nhắn tin với người dùng hiện tại
        sent_messages = Message.objects.filter(sender=request.user)
        received_messages = Message.objects.filter(receiver=request.user)
        
        # Lấy ID của tất cả người đã từng tương tác
        sender_ids = received_messages.values_list('sender', flat=True).distinct()
        receiver_ids = sent_messages.values_list('receiver', flat=True).distinct()
        
        # Kết hợp tất cả ID thành một danh sách duy nhất
        user_ids = set(list(sender_ids) + list(receiver_ids))
        
        # Loại bỏ ID của người dùng hiện tại nếu có
        if request.user.id in user_ids:
            user_ids.remove(request.user.id)
        
        # Lấy thông tin chi tiết của người dùng
        conversation_users = User.objects.filter(id__in=user_ids)
        
        # Lấy tin nhắn gần nhất và số tin nhắn chưa đọc cho mỗi cuộc trò chuyện
        conversations = []
        for user in conversation_users:
            # Lấy tin nhắn gần nhất
            latest_message = Message.objects.filter(
                (Q(sender=request.user) & Q(receiver=user)) | 
                (Q(sender=user) & Q(receiver=request.user))
            ).order_by('-created_at').first()
            
            # Đếm số tin nhắn chưa đọc
            unread_count = Message.objects.filter(
                sender=user,
                receiver=request.user,
                is_read=False
            ).count()
            
            if latest_message:
                conversations.append({
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'avatar': user.avatar.url if user.avatar else None
                    },
                    'latest_message': {
                        'content': latest_message.content,
                        'timestamp': latest_message.created_at,
                        'is_from_me': latest_message.sender == request.user
                    },
                    'unread_count': unread_count
                })
        
        # Sắp xếp theo thời gian tin nhắn gần nhất
        conversations.sort(key=lambda x: x['latest_message']['timestamp'], reverse=True)
        
        return Response(conversations)

class ConversationDetailView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        other_user_id = self.kwargs['user_id']
        
        # Đánh dấu tin nhắn là đã đọc khi xem chi tiết cuộc trò chuyện
        unread_messages = Message.objects.filter(
            sender_id=other_user_id,
            receiver=user,
            is_read=False
        )
        
        for message in unread_messages:
            message.is_read = True
            message.save(update_fields=['is_read'])
            
        return Message.objects.filter(
            (Q(sender=user) & Q(receiver_id=other_user_id)) |
            (Q(receiver=user) & Q(sender_id=other_user_id))
        ).order_by('timestamp')

# API cho User báo cáo tin nhắn
class ReportMessageView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageReportCreateSerializer
    
    def perform_create(self, serializer):
        message_id = self.request.data.get('message')
        message = get_object_or_404(Message, id=message_id)
        
        # Kiểm tra xem người báo cáo có phải là người tham gia cuộc trò chuyện không
        if message.sender != self.request.user and message.receiver != self.request.user:
            return Response(
                {"error": "Bạn không thể báo cáo tin nhắn mà bạn không phải là người tham gia"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Kiểm tra xem đã báo cáo trước đó chưa
        if MessageReport.objects.filter(message=message, reporter=self.request.user).exists():
            return Response(
                {"error": "Bạn đã báo cáo tin nhắn này trước đó"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Lưu báo cáo và cập nhật trạng thái tin nhắn
        report = serializer.save(reporter=self.request.user)
        message.content_status = 'REPORTED'
        message.save(update_fields=['content_status'])
        
        return Response(
            MessageReportSerializer(report).data,
            status=status.HTTP_201_CREATED
        )

# API cho Admin quản lý tin nhắn
class AdminMessageListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminMessageSerializer
    queryset = Message.objects.all().order_by('-timestamp')
    filter_backends = [filters.SearchFilter]
    search_fields = ['content', 'sender__username', 'receiver__username']
    
    def get_queryset(self):
        queryset = Message.objects.all().order_by('-timestamp')
        
        # Lọc theo trạng thái nội dung
        content_status = self.request.query_params.get('content_status')
        if content_status:
            queryset = queryset.filter(content_status=content_status)
            
        # Lọc theo loại tin nhắn
        message_type = self.request.query_params.get('message_type')
        if message_type:
            queryset = queryset.filter(message_type=message_type)
            
        # Lọc theo người gửi
        sender_id = self.request.query_params.get('sender_id')
        if sender_id:
            queryset = queryset.filter(sender_id=sender_id)
            
        # Lọc theo người nhận
        receiver_id = self.request.query_params.get('receiver_id')
        if receiver_id:
            queryset = queryset.filter(receiver_id=receiver_id)
            
        # Lọc theo khoảng thời gian
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(timestamp__range=[start_date, end_date])
            
        return queryset

class AdminMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminMessageSerializer
    queryset = Message.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Lưu lại thông tin người review
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        # Ghi log trước khi xóa
        print(f"Admin {self.request.user.username} đã xóa tin nhắn {instance.id} từ {instance.sender.username} đến {instance.receiver.username}")
        instance.delete()

class AdminMessageReportListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = MessageReportSerializer
    queryset = MessageReport.objects.all().order_by('-timestamp')
    filter_backends = [filters.SearchFilter]
    search_fields = ['description', 'reporter__username', 'message__content']
    
    def get_queryset(self):
        queryset = MessageReport.objects.all().order_by('-timestamp')
        
        # Lọc theo trạng thái
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Lọc theo lý do
        reason = self.request.query_params.get('reason')
        if reason:
            queryset = queryset.filter(reason=reason)
            
        return queryset

class AdminMessageReportDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = MessageReportSerializer
    queryset = MessageReport.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = MessageReportUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Lưu thông tin người xử lý
        instance.handled_by = request.user
        instance.handled_at = timezone.now()
        
        self.perform_update(serializer)
        
        # Cập nhật trạng thái tin nhắn nếu cần
        if instance.status in ['REVIEWED', 'RESOLVED']:
            message = instance.message
            message.content_status = 'REVIEWED'
            message.reviewed_by = request.user
            message.reviewed_at = timezone.now()
            message.save(update_fields=['content_status', 'reviewed_by', 'reviewed_at'])
        
        return Response(MessageReportSerializer(instance).data)

class AdminChatRestrictionListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ChatRestrictionSerializer
    queryset = ChatRestriction.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChatRestrictionCreateSerializer
        return ChatRestrictionSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class AdminChatRestrictionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ChatRestrictionSerializer
    queryset = ChatRestriction.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = True  # Chỉ cập nhật các trường được cung cấp
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)

class AdminUserChatStatsView(APIView):
    """API để xem thống kê chat của người dùng"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, user_id=None):
        if user_id:
            # Thống kê cho một người dùng cụ thể
            user = get_object_or_404(User, id=user_id)
            
            sent_count = Message.objects.filter(sender=user).count()
            received_count = Message.objects.filter(receiver=user).count()
            
            # Người dùng nhắn tin nhiều nhất với ai
            most_messaged = Message.objects.filter(
                Q(sender=user) | Q(receiver=user)
            ).values(
                'sender_id', 'receiver_id'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            most_messaged_users = []
            for item in most_messaged:
                other_user_id = item['receiver_id'] if item['sender_id'] == user.id else item['sender_id']
                try:
                    other_user = User.objects.get(id=other_user_id)
                    most_messaged_users.append({
                        'id': other_user.id,
                        'username': other_user.username,
                        'message_count': item['count']
                    })
                except User.DoesNotExist:
                    continue
            
            return Response({
                'user_id': user.id,
                'username': user.username,
                'sent_count': sent_count,
                'received_count': received_count,
                'total_count': sent_count + received_count,
                'most_messaged_users': most_messaged_users
            })
        else:
            # Thống kê tổng quan cho tất cả người dùng
            top_chatters = User.objects.annotate(
                sent_count=Count('chat_sent_messages'),
                received_count=Count('chat_received_messages')
            ).annotate(
                total_count=Count('chat_sent_messages') + Count('chat_received_messages')
            ).order_by('-total_count')[:10]
            
            result = []
            for user in top_chatters:
                result.append({
                    'user_id': user.id,
                    'username': user.username,
                    'sent_count': user.sent_count,
                    'received_count': user.received_count,
                    'total_count': user.total_count
                })
            
            total_messages = Message.objects.count()
            users_with_messages = User.objects.filter(
                Q(chat_sent_messages__isnull=False) | Q(chat_received_messages__isnull=False)
            ).distinct().count()
            
            return Response({
                'total_messages': total_messages,
                'users_with_messages': users_with_messages,
                'top_chatters': result
            })

class AdminMessageReportStatsView(APIView):
    """API hiển thị thống kê về báo cáo tin nhắn vi phạm cho admin"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, format=None):
        # Lấy tham số từ request
        period = request.query_params.get('period', 'month')  # Mặc định là thống kê theo tháng
        
        # Xác định khoảng thời gian dựa trên period
        now = timezone.now()
        if period == 'week':
            start_date = now - timedelta(days=7)
            period_label = '7 ngày qua'
        elif period == 'month':
            start_date = now - timedelta(days=30)
            period_label = '30 ngày qua'
        elif period == 'year':
            start_date = now - timedelta(days=365)
            period_label = '365 ngày qua'
        else:  # Mặc định là all
            start_date = None
            period_label = 'Tất cả thời gian'
        
        # Filter theo thời gian
        if start_date:
            reports = MessageReport.objects.filter(timestamp__gte=start_date)
        else:
            reports = MessageReport.objects.all()
        
        # Tổng số báo cáo
        total_reports = reports.count()
        
        # Thống kê theo trạng thái
        status_stats = reports.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        status_data = {}
        for item in status_stats:
            status_data[item['status']] = item['count']
        
        # Thống kê theo lý do báo cáo
        reason_stats = reports.values('reason').annotate(
            count=Count('id')
        ).order_by('reason')
        
        reason_data = {}
        for item in reason_stats:
            reason_data[item['reason']] = item['count']
        
        # Thống kê thời gian xử lý
        # Những báo cáo đã xử lý (có handled_at)
        handled_reports = reports.exclude(handled_at=None)
        
        handling_times = []
        for report in handled_reports:
            # Tính thời gian từ lúc báo cáo đến lúc xử lý (giờ)
            if report.handled_at:  # Kiểm tra để tránh lỗi None
                duration = (report.handled_at - report.timestamp).total_seconds() / 3600
                handling_times.append(duration)
        
        avg_handling_time = 0
        if handling_times:
            avg_handling_time = sum(handling_times) / len(handling_times)
        
        # Top người dùng báo cáo nhiều nhất
        top_reporters = reports.values('reporter').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        top_reporters_data = []
        for item in top_reporters:
            try:
                user = User.objects.get(id=item['reporter'])
                top_reporters_data.append({
                    'user_id': user.id,
                    'username': user.username,
                    'report_count': item['count']
                })
            except User.DoesNotExist:
                continue
        
        # Top người dùng bị báo cáo nhiều nhất
        # Lấy tin nhắn và người gửi từ báo cáo
        message_ids = reports.values_list('message', flat=True)
        messages = Message.objects.filter(id__in=message_ids)
        
        reported_users = {}
        for message in messages:
            sender_id = message.sender.id
            if sender_id in reported_users:
                reported_users[sender_id] += 1
            else:
                reported_users[sender_id] = 1
        
        # Sắp xếp và lấy top 5
        sorted_reported_users = sorted(reported_users.items(), key=lambda x: x[1], reverse=True)[:5]
        
        top_reported_data = []
        for user_id, count in sorted_reported_users:
            try:
                user = User.objects.get(id=user_id)
                top_reported_data.append({
                    'user_id': user.id,
                    'username': user.username,
                    'report_count': count
                })
            except User.DoesNotExist:
                continue
        
        # Phân tích xu hướng theo thời gian
        trend_list = []
        
        if period in ['week', 'month'] and start_date is not None:
            # Thống kê theo ngày
            trend_data = {}
            current_date = start_date
            while current_date <= now:
                date_str = current_date.strftime('%Y-%m-%d')
                trend_data[date_str] = 0
                current_date += timedelta(days=1)
            
            # Đếm báo cáo theo ngày
            for report in reports:
                date_str = report.timestamp.strftime('%Y-%m-%d')
                if date_str in trend_data:
                    trend_data[date_str] += 1
            
            # Chuyển đổi thành list để dễ sử dụng
            trend_list = [
                {'date': date, 'count': count}
                for date, count in trend_data.items()
            ]
            
        elif period == 'year' and start_date is not None:
            # Thống kê theo tháng
            trend_data = {}
            current_date = start_date
            while current_date <= now:
                month_str = current_date.strftime('%Y-%m')
                trend_data[month_str] = 0
                
                # Tăng lên tháng tiếp theo
                year = current_date.year
                month = current_date.month
                
                if month == 12:
                    current_date = current_date.replace(year=year+1, month=1)
                else:
                    current_date = current_date.replace(month=month+1)
            
            # Đếm báo cáo theo tháng
            for report in reports:
                month_str = report.timestamp.strftime('%Y-%m')
                if month_str in trend_data:
                    trend_data[month_str] += 1
            
            # Chuyển đổi thành list
            trend_list = [
                {'month': month, 'count': count}
                for month, count in trend_data.items()
            ]
            
        else:  # all time
            # Thống kê theo năm
            trend_data = {}
            earliest_year = now.year
            
            if MessageReport.objects.exists():
                earliest_report = MessageReport.objects.earliest('timestamp')
                if earliest_report and earliest_report.timestamp:
                    earliest_year = earliest_report.timestamp.year
            
            for year in range(earliest_year, now.year + 1):
                trend_data[str(year)] = 0
            
            # Đếm báo cáo theo năm
            for report in reports:
                if report.timestamp:  # Kiểm tra để tránh lỗi None
                    year_str = str(report.timestamp.year)
                    if year_str in trend_data:
                        trend_data[year_str] += 1
            
            # Chuyển đổi thành list
            trend_list = [
                {'year': year, 'count': count}
                for year, count in trend_data.items()
            ]
        
        return Response({
            'period': period_label,
            'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'total_reports': total_reports,
            'status_stats': status_data,
            'reason_stats': reason_data,
            'avg_handling_time_hours': round(avg_handling_time, 2),
            'top_reporters': top_reporters_data,
            'top_reported_users': top_reported_data,
            'trend_data': trend_list
        })

class AdminPendingReportsView(APIView):
    """API hiển thị danh sách báo cáo đang chờ xử lý cho admin"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, format=None):
        # Lấy tham số từ request
        reason = request.query_params.get('reason')  # Filter theo lý do (tùy chọn)
        
        # Lấy các báo cáo đang chờ xử lý (status=PENDING)
        pending_reports = MessageReport.objects.filter(status='PENDING').order_by('-timestamp')
        
        # Áp dụng filter theo lý do nếu có
        if reason:
            pending_reports = pending_reports.filter(reason=reason)
        
        # Group các báo cáo theo người dùng bị báo cáo
        reported_users = {}
        
        for report in pending_reports:
            try:
                # Lấy người gửi tin nhắn (người bị báo cáo)
                reported_user = report.message.sender
                reported_user_id = reported_user.id
                
                # Thêm vào dictionary hoặc tạo mới
                if reported_user_id in reported_users:
                    reported_users[reported_user_id]['reports'].append({
                        'id': report.id,
                        'reason': report.reason,
                        'description': report.description,
                        'timestamp': report.timestamp,
                        'message_id': report.message.id,
                        'message_content': report.message.content,
                        'reporter': {
                            'id': report.reporter.id,
                            'username': report.reporter.username
                        }
                    })
                    reported_users[reported_user_id]['count'] += 1
                else:
                    reported_users[reported_user_id] = {
                        'user': {
                            'id': reported_user.id,
                            'username': reported_user.username,
                            'email': reported_user.email,
                        },
                        'reports': [{
                            'id': report.id,
                            'reason': report.reason,
                            'description': report.description,
                            'timestamp': report.timestamp,
                            'message_id': report.message.id,
                            'message_content': report.message.content,
                            'reporter': {
                                'id': report.reporter.id,
                                'username': report.reporter.username
                            }
                        }],
                        'count': 1
                    }
            except:
                # Skip nếu có lỗi (người dùng không tồn tại, v.v.)
                continue
        
        # Chuyển đổi dictionary thành list và sắp xếp theo số lượng báo cáo
        result = []
        for user_id, data in reported_users.items():
            result.append(data)
        
        result = sorted(result, key=lambda x: x['count'], reverse=True)
        
        return Response({
            'total_pending': pending_reports.count(),
            'reported_users': result
        })

class UnreadCountView(APIView):
    """API để lấy số lượng tin nhắn chưa đọc"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Đếm số tin nhắn chưa đọc của người dùng hiện tại
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        # Đếm số tin nhắn chưa đọc theo từng người gửi
        unread_by_sender = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).values('sender').annotate(count=Count('id')).order_by()
        
        sender_details = []
        for item in unread_by_sender:
            try:
                sender = User.objects.get(id=item['sender'])
                sender_details.append({
                    'sender_id': sender.id,
                    'sender_username': sender.username,
                    'count': item['count']
                })
            except User.DoesNotExist:
                pass
        
        return Response({
            'total_unread': unread_count,
            'unread_by_sender': sender_details
        })

class MarkReadView(APIView):
    """API để đánh dấu tin nhắn là đã đọc"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, username):
        other_user = get_object_or_404(User, username=username)
        
        # Đánh dấu tất cả tin nhắn từ người dùng cụ thể là đã đọc
        updated_count = Message.objects.filter(
            sender=other_user,
            receiver=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'success': True,
            'marked_read': updated_count
        })

class RecentConversationsView(APIView):
    """API để lấy các cuộc trò chuyện gần đây"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Giới hạn chỉ lấy 5 cuộc trò chuyện gần nhất
        limit = request.query_params.get('limit', 5)
        try:
            limit = int(limit)
        except ValueError:
            limit = 5
        
        # Lấy thông tin người dùng đã nhắn tin với người dùng hiện tại
        conversation_users = User.objects.filter(
            Q(sent_messages__receiver=request.user) | Q(received_messages__sender=request.user)
        ).distinct()
        
        # Lấy tin nhắn gần nhất và số tin nhắn chưa đọc cho mỗi cuộc trò chuyện
        conversations = []
        for user in conversation_users:
            # Lấy tin nhắn gần nhất
            latest_message = Message.objects.filter(
                (Q(sender=request.user) & Q(receiver=user)) | 
                (Q(sender=user) & Q(receiver=request.user))
            ).order_by('-created_at').first()
            
            # Đếm số tin nhắn chưa đọc
            unread_count = Message.objects.filter(
                sender=user,
                receiver=request.user,
                is_read=False
            ).count()
            
            if latest_message:
                conversations.append({
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'avatar': user.avatar.url if user.avatar else None
                    },
                    'latest_message': {
                        'content': latest_message.content,
                        'timestamp': latest_message.created_at,
                        'is_from_me': latest_message.sender == request.user
                    },
                    'unread_count': unread_count,
                    'timestamp': latest_message.created_at  # Để sắp xếp
                })
        
        # Sắp xếp theo thời gian tin nhắn gần nhất
        conversations.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Giới hạn số lượng
        conversations = conversations[:limit]
        
        # Loại bỏ trường timestamp đã dùng để sắp xếp
        for conv in conversations:
            del conv['timestamp']
        
        return Response(conversations)

# Admin APIs for chat restrictions

class ChatRestrictionListView(generics.ListCreateAPIView):
    """API để xem danh sách và tạo mới hạn chế chat (chỉ dành cho admin)"""
    serializer_class = ChatRestrictionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return ChatRestriction.objects.all().order_by('-created_at')

class ChatRestrictionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API để xem chi tiết, cập nhật và xóa hạn chế chat (chỉ dành cho admin)"""
    serializer_class = ChatRestrictionSerializer
    permission_classes = [IsAdminUser]
    queryset = ChatRestriction.objects.all()

class RestrictUserView(APIView):
    """API để hạn chế người dùng chat (chỉ dành cho admin)"""
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        # Lấy thông tin hạn chế từ request
        restriction_type = request.data.get('restriction_type', 'TEMPORARY')
        reason = request.data.get('reason', 'Violation of community guidelines')
        
        # Tạo thời gian hết hạn nếu là hạn chế tạm thời
        expires_at = None
        if restriction_type == 'TEMPORARY':
            duration_days = request.data.get('duration_days', 7)
            expires_at = timezone.now() + timezone.timedelta(days=duration_days)
        
        # Tạo hạn chế mới
        restriction = ChatRestriction.objects.create(
            user=user,
            restriction_type=restriction_type,
            reason=reason,
            expires_at=expires_at,
            is_active=True,
            restricted_by=request.user
        )
        
        serializer = ChatRestrictionSerializer(restriction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UnrestrictUserView(APIView):
    """API để hủy hạn chế người dùng chat (chỉ dành cho admin)"""
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        # Hủy tất cả hạn chế đang hoạt động
        updated = ChatRestriction.objects.filter(user=user, is_active=True).update(
            is_active=False,
            unrestricted_by=request.user,
            unrestricted_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'Removed {updated} active restrictions for user {user.username}'
        })
