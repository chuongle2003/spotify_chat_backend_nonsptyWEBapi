"""
WebSocket consumers for AI Assistant app
"""
import json
import logging
import traceback
from typing import Dict, Optional, Any
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from .models import AIConversation, AIMessage
from .gemini_client import GeminiClient

User = get_user_model()
logger = logging.getLogger(__name__)

class AIChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time AI chat interactions"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.conversation_id = None
        self.conversation_group_name = None
        self.channel_layer = get_channel_layer()
        
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        # Verify authentication
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Get conversation ID from URL
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        
        # Create group name for this conversation
        self.conversation_group_name = f'ai_chat_{self.conversation_id}'
        
        # Verify user has access to this conversation if conversation_id provided
        if self.conversation_id:
            has_access = await self.user_has_access_to_conversation(
                user=self.user,
                conversation_id=self.conversation_id
            )
            
            if not has_access:
                await self.close(code=4003)
                return
        
        # Join conversation group
        if self.channel_layer:
            await self.channel_layer.group_add(
                self.conversation_group_name,
                self.channel_name
            )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave conversation group
        if self.conversation_group_name and self.channel_layer:
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages received from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            else:
                await self.send(text_data=json.dumps({
                    'error': f'Unknown message type: {message_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in AIChatConsumer.receive: {str(e)}")
            logger.error(traceback.format_exc())
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def handle_message(self, data):
        """Process incoming chat message"""
        try:
            prompt = data.get('message', '')
            system_context = data.get('system_context')
            conversation_id = data.get('conversation_id') or self.conversation_id
            
            # Get or create conversation
            if conversation_id:
                conversation = await self.get_conversation(conversation_id)
                if not conversation:
                    # Create new conversation if ID not found
                    conversation = await self.create_conversation(
                        user=self.user,
                        title=prompt[:50] + "..." if len(prompt) > 50 else prompt,
                        system_context=system_context
                    )
            else:
                # Create new conversation
                conversation = await self.create_conversation(
                    user=self.user,
                    title=prompt[:50] + "..." if len(prompt) > 50 else prompt,
                    system_context=system_context
                )
            
            # Update the conversation ID if it was newly created
            if not self.conversation_id:
                self.conversation_id = conversation.id
                self.conversation_group_name = f'ai_chat_{self.conversation_id}'
                
                # Join the new conversation group
                if self.channel_layer:
                    await self.channel_layer.group_add(
                        self.conversation_group_name,
                        self.channel_name
                    )
            
            # Save user message
            await self.save_message(
                conversation=conversation,
                role='user',
                content=prompt
            )
            
            # Send message to group to handle real-time display
            if self.channel_layer:
                user_id = self.user.id if self.user and hasattr(self.user, 'id') else None
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'chat_message',
                        'message': prompt,
                        'role': 'user',
                        'user_id': user_id,
                        'conversation_id': conversation.id
                    }
                )
            
            # Generate AI response (non-blocking)
            await self.generate_ai_response(conversation, prompt, system_context)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            logger.error(traceback.format_exc())
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def generate_ai_response(self, conversation, prompt, system_context=None):
        """Generate AI response in a non-blocking way"""
        try:
            # Send typing indicator
            if self.channel_layer:
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'typing_indicator',
                        'is_typing': True,
                        'role': 'assistant'
                    }
                )
            
            # Get conversation history
            history = await self.get_conversation_history(conversation)
            
            # Initialize Gemini client
            client = GeminiClient()
            
            # Use system context from conversation if not explicitly provided
            if not system_context and conversation.system_context:
                system_context = conversation.system_context
            
            # Generate response
            if len(history) > 1:
                # Use chat history for context
                response = client.generate_chat_response(
                    history=history,
                    system_instructions=system_context
                )
            else:
                # Simple response for first message
                response = client.generate_text_response(
                    prompt=prompt,
                    context=system_context
                )
            
            # Save assistant response
            await self.save_message(
                conversation=conversation,
                role='assistant',
                content=response
            )
            
            # Send response to the group
            if self.channel_layer:
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'chat_message',
                        'message': response,
                        'role': 'assistant',
                        'conversation_id': conversation.id
                    }
                )
            
            # Turn off typing indicator
            if self.channel_layer:
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'typing_indicator',
                        'is_typing': False,
                        'role': 'assistant'
                    }
                )
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Send error message
            error_message = f"Sorry, I encountered an error: {str(e)}"
            await self.save_message(
                conversation=conversation,
                role='assistant',
                content=error_message
            )
            
            if self.channel_layer:
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'chat_message',
                        'message': error_message,
                        'role': 'assistant',
                        'conversation_id': conversation.id,
                        'is_error': True
                    }
                )
            
            # Turn off typing indicator
            if self.channel_layer:
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'typing_indicator',
                        'is_typing': False,
                        'role': 'assistant'
                    }
                )
    
    async def handle_typing(self, data):
        """Handle typing indicator events"""
        is_typing = data.get('is_typing', False)
        
        # Broadcast typing status to group
        if self.channel_layer:
            user_id = self.user.id if self.user and hasattr(self.user, 'id') else None
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'typing_indicator',
                    'is_typing': is_typing,
                    'user_id': user_id,
                    'role': 'user'
                }
            )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'role': event['role'],
            'conversation_id': event.get('conversation_id'),
            'user_id': event.get('user_id'),
            'is_error': event.get('is_error', False)
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator status to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'is_typing': event['is_typing'],
            'role': event['role'],
            'user_id': event.get('user_id')
        }))
    
    @database_sync_to_async
    def user_has_access_to_conversation(self, user, conversation_id):
        """Check if user has access to the specified conversation"""
        try:
            return AIConversation.objects.filter(
                id=conversation_id, 
                user=user
            ).exists()
        except Exception:
            return False
    
    @database_sync_to_async
    def get_conversation(self, conversation_id):
        """Get conversation by ID if user has access"""
        try:
            return AIConversation.objects.get(id=conversation_id, user=self.user)
        except AIConversation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_conversation(self, user, title, system_context=None):
        """Create a new conversation"""
        return AIConversation.objects.create(
            user=user,
            title=title,
            system_context=system_context
        )
    
    @database_sync_to_async
    def save_message(self, conversation, role, content):
        """Save message to database"""
        return AIMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content
        )
    
    @database_sync_to_async
    def get_conversation_history(self, conversation):
        """Get all messages for a conversation"""
        messages = AIMessage.objects.filter(conversation=conversation).order_by('created_at')
        return [{'role': msg.role, 'content': msg.content} for msg in messages]