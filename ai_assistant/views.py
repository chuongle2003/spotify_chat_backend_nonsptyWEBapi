"""
Views for the AI Assistant app
"""
import logging
import json
import base64
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse

from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, permission_classes

from .models import AIConversation, AIMessage, AISystemPrompt
from .serializers import (
    AIConversationSerializer, 
    AIMessageSerializer,
    AISystemPromptSerializer,
    AITextRequestSerializer,
    AIMultiModalRequestSerializer,
    AIResponseSerializer,
)
from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# HTML Views
def ai_chat_view(request):
    """Render the AI chat interface"""
    return render(request, 'ai_chat.html')

def ai_guide_view(request):
    """Render the AI guide page"""
    return render(request, 'ai_guide.html')

# API Views
class AISystemPromptViewSet(viewsets.ModelViewSet):
    """API endpoint for system prompts"""
    queryset = AISystemPrompt.objects.all()
    serializer_class = AISystemPromptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return all system prompts"""
        return AISystemPrompt.objects.all()

class AIConversationViewSet(viewsets.ModelViewSet):
    """API endpoint for AI conversations"""
    serializer_class = AIConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return conversations for the current user"""
        return AIConversation.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a specific conversation"""
        conversation = self.get_object()
        messages = AIMessage.objects.filter(conversation=conversation)
        serializer = AIMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def clear(self, request, pk=None):
        """Clear all messages in a conversation but keep the conversation"""
        conversation = self.get_object()
        # Keep only system messages if they exist
        AIMessage.objects.filter(conversation=conversation).exclude(role='system').delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AITextRequestView(APIView):
    """API view for handling text-based AI requests"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle text requests to the AI assistant"""
        serializer = AITextRequestSerializer(data=request.data)
        validated_data = {}
        
        if serializer.is_valid():
            validated_data = serializer.validated_data
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            gemini_client = GeminiClient()
            prompt = validated_data.get('prompt')
            if not prompt:
                return Response(
                    {'error': 'Prompt is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            conversation_id = validated_data.get('conversation_id')
            system_context = validated_data.get('system_context')
            
            # Handle conversation context
            if conversation_id:
                # Continue existing conversation
                conversation = get_object_or_404(
                    AIConversation, id=conversation_id, user=request.user
                )
                
                # Get conversation history
                history = []
                for msg in AIMessage.objects.filter(conversation=conversation).order_by('created_at'):
                    history.append({'role': msg.role, 'content': msg.content})
                
                # Add the current message
                history.append({'role': 'user', 'content': prompt})
                
                # Save user message
                AIMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=prompt
                )
                
                # Get system context from conversation if not provided
                if not system_context and conversation.system_context:
                    system_context = conversation.system_context
                
                # Generate response with conversation history
                ai_response = gemini_client.generate_chat_response(
                    history=history,
                    system_instructions=system_context
                )
            else:
                # Create a new conversation
                conversation = AIConversation.objects.create(
                    user=request.user,
                    title=prompt[:50] + "..." if len(prompt) > 50 else prompt,
                    system_context=system_context
                )
                
                # Save user message
                AIMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=prompt
                )
                
                # Generate simple response
                ai_response = gemini_client.generate_text_response(
                    prompt=prompt,
                    context=system_context
                )
            
            # Save assistant response
            AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=ai_response
            )
            
            # Return the response
            response_serializer = AIResponseSerializer({
                'response': ai_response,
                'conversation_id': conversation.id
            })
            return Response(response_serializer.data)
        
        except Exception as e:
            logger.error(f"Error in AI text request: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AIMultiModalRequestView(APIView):
    """API view for handling multimodal (text + image) AI requests"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle multimodal requests to the AI assistant"""
        serializer = AIMultiModalRequestSerializer(data=request.data)
        validated_data = {}
        
        if serializer.is_valid():
            validated_data = serializer.validated_data
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            gemini_client = GeminiClient()
            prompt = validated_data.get('prompt')
            if not prompt:
                return Response(
                    {'error': 'Prompt is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            image = validated_data.get('image')
            if not image:
                return Response(
                    {'error': 'Image is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            conversation_id = validated_data.get('conversation_id')
            system_context = validated_data.get('system_context')
            
            # Read image data
            image_data = base64.b64encode(image.read()).decode('utf-8')
            
            # Handle conversation
            if conversation_id:
                conversation = get_object_or_404(
                    AIConversation, id=conversation_id, user=request.user
                )
            else:
                conversation = AIConversation.objects.create(
                    user=request.user,
                    title=prompt[:50] + "..." if len(prompt) > 50 else prompt,
                    system_context=system_context
                )
            
            # Save user message with image flag
            AIMessage.objects.create(
                conversation=conversation,
                role='user',
                content=prompt,
                has_image=True
            )
            
            # Get system context from conversation if not provided
            if not system_context and conversation.system_context:
                system_context = conversation.system_context
            
            # Generate response
            ai_response = gemini_client.generate_multimodal_response(
                prompt=prompt,
                image_data=image_data,
                context=system_context
            )
            
            # Save assistant response
            AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=ai_response
            )
            
            # Return response
            response_serializer = AIResponseSerializer({
                'response': ai_response,
                'conversation_id': conversation.id
            })
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Error in AI multimodal request: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SystemInstructionsView(APIView):
    """API view for getting predefined system instructions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get default system instructions for the AI"""
        # Hard-coded system contexts for different use cases
        contexts = {
            "general": "You are a helpful AI assistant that can answer questions about the Spotify Chat system. Answer concisely and accurately.",
            "music": "You are a music assistant that can help users discover new music, understand genres, and learn about artists. Focus on providing music-related information.",
            "chat": "You are a chat assistant that can help users understand how to use the chat features of the Spotify Chat app.",
            "playlists": "You are a playlist assistant that helps users manage and discover music playlists.",
            "technical": "You are a technical assistant that can help developers understand the API and backend details of the Spotify Chat app."
        }
        
        # Return available system contexts
        return Response(contexts)