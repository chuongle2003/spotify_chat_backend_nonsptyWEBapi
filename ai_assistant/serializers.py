"""
Serializers for the AI Assistant app
"""
from rest_framework import serializers
from .models import AIConversation, AIMessage, AISystemPrompt

class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer for individual AI messages"""
    
    class Meta:
        model = AIMessage
        fields = ['id', 'role', 'content', 'created_at', 'has_image']
        read_only_fields = ['id', 'created_at']

class AIConversationSerializer(serializers.ModelSerializer):
    """Serializer for AI conversations"""
    messages = AIMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = AIConversation
        fields = ['id', 'title', 'user', 'system_context', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create a new conversation and associate it with the current user"""
        user = self.context['request'].user
        conversation = AIConversation.objects.create(user=user, **validated_data)
        return conversation

class AISystemPromptSerializer(serializers.ModelSerializer):
    """Serializer for system prompts"""
    
    class Meta:
        model = AISystemPrompt
        fields = ['id', 'name', 'description', 'prompt_text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AITextRequestSerializer(serializers.Serializer):
    """Serializer for text-only AI requests"""
    prompt = serializers.CharField(required=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    system_context = serializers.CharField(required=False, allow_null=True, allow_blank=True)

class AIMultiModalRequestSerializer(serializers.Serializer):
    """Serializer for multimodal (text + image) AI requests"""
    prompt = serializers.CharField(required=True)
    image = serializers.ImageField(required=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    system_context = serializers.CharField(required=False, allow_null=True, allow_blank=True)

class AIResponseSerializer(serializers.Serializer):
    """Serializer for AI generated responses"""
    response = serializers.CharField()
    conversation_id = serializers.IntegerField(required=False, allow_null=True) 