from rest_framework import serializers
from .models import Message
from music.models import User, Song, Playlist
from music.serializers import SongSerializer, PlaylistSerializer, UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    shared_song = SongSerializer(read_only=True)
    shared_playlist = PlaylistSerializer(read_only=True)
    receiver_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 
            'sender', 
            'receiver',
            'receiver_id',
            'content', 
            'timestamp', 
            'is_read',
            'message_type',
            'attachment',
            'image',
            'voice_note',
            'shared_song',
            'shared_playlist'
        ]
        read_only_fields = ['sender', 'timestamp', 'is_read']

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

class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['other_user', 'last_message', 'unread_count']

    def get_other_user(self, obj):
        request_user = self.context['request'].user
        other_user = obj.sender if obj.sender != request_user else obj.receiver
        return UserSerializer(other_user).data

    def get_last_message(self, obj):
        return {
            'content': obj.content,
            'timestamp': obj.timestamp,
            'message_type': obj.message_type
        }

    def get_unread_count(self, obj):
        request_user = self.context['request'].user
        other_user = obj.sender if obj.sender != request_user else obj.receiver
        return Message.objects.filter(
            sender=other_user,
            receiver=request_user,
            is_read=False
        ).count() 