from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Message, MessageReport, ChatRestriction
from music.models import User, Song, Playlist
from music.serializers import SongSerializer, PlaylistSerializer, UserSerializer, SongBasicSerializer, PlaylistBasicSerializer

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'avatar')

class MessageSerializer(serializers.ModelSerializer):
    sender_info = UserBasicSerializer(source='sender', read_only=True)
    receiver_info = UserBasicSerializer(source='receiver', read_only=True)
    shared_song_info = SongBasicSerializer(source='shared_song', read_only=True)
    shared_playlist_info = PlaylistBasicSerializer(source='shared_playlist', read_only=True)
    
    class Meta:
        model = Message
        fields = ('id', 'sender', 'receiver', 'content', 'timestamp', 'is_read', 
                  'message_type', 'attachment', 'image', 'voice_note', 'shared_song', 
                  'shared_playlist', 'sender_info', 'receiver_info', 'shared_song_info', 
                  'shared_playlist_info')
        read_only_fields = ('sender', 'timestamp', 'is_read')

class AdminMessageSerializer(serializers.ModelSerializer):
    sender_info = UserBasicSerializer(source='sender', read_only=True)
    receiver_info = UserBasicSerializer(source='receiver', read_only=True)
    shared_song_info = SongBasicSerializer(source='shared_song', read_only=True)
    shared_playlist_info = PlaylistBasicSerializer(source='shared_playlist', read_only=True)
    reviewed_by_info = UserBasicSerializer(source='reviewed_by', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'sender', 'receiver', 'content', 'timestamp', 'is_read', 
                  'message_type', 'attachment', 'image', 'voice_note', 'shared_song', 
                  'shared_playlist', 'sender_info', 'receiver_info', 'shared_song_info', 
                  'shared_playlist_info', 'content_status', 'review_note', 'reviewed_by', 
                  'reviewed_at', 'reviewed_by_info')

class MessageReportSerializer(serializers.ModelSerializer):
    reporter_info = UserBasicSerializer(source='reporter', read_only=True)
    message_detail = MessageSerializer(source='message', read_only=True)
    handled_by_info = UserBasicSerializer(source='handled_by', read_only=True)
    
    class Meta:
        model = MessageReport
        fields = ('id', 'message', 'reporter', 'reason', 'description', 'timestamp', 
                  'status', 'handled_by', 'handled_at', 'action_taken', 
                  'reporter_info', 'message_detail', 'handled_by_info')
        read_only_fields = ('message', 'reporter', 'timestamp')

class MessageReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReport
        fields = ('message', 'reason', 'description')

class MessageReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReport
        fields = ('status', 'action_taken')

class ChatRestrictionSerializer(serializers.ModelSerializer):
    user_info = UserBasicSerializer(source='user', read_only=True)
    created_by_info = UserBasicSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = ChatRestriction
        fields = ('id', 'user', 'restriction_type', 'reason', 'created_at', 
                  'expires_at', 'created_by', 'is_active', 'user_info', 'created_by_info')
        read_only_fields = ('created_at',)

class ChatRestrictionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRestriction
        fields = ('user', 'restriction_type', 'reason', 'expires_at')

class ConversationSerializer(serializers.ModelSerializer):
    partner = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ('id', 'partner', 'last_message', 'timestamp')
    
    def get_partner(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        
        user = request.user
        partner = obj.sender if obj.sender != user else obj.receiver
        return UserBasicSerializer(partner).data
    
    def get_last_message(self, obj):
        return {
            'content': obj.content,
            'message_type': obj.message_type,
            'timestamp': obj.timestamp,
            'is_read': obj.is_read
        }

    def validate_receiver_id(self, value):
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Người nhận không tồn tại")

    def create(self, validated_data):
        receiver_id = validated_data.pop('receiver_id')
        receiver = User.objects.get(id=receiver_id)
        return Message.objects.create(receiver=receiver, **validated_data) 