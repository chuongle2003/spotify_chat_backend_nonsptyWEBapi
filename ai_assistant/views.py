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

class APIDocumentationView(APIView):
    """API endpoint để hiển thị tất cả API có trong dự án"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Hiển thị danh sách đầy đủ các API trong hệ thống với mô tả và cấu trúc request/response"""
        
        api_documentation = {
            "api_version": "v1",
            "description": "Tài liệu API cho Spotify Chat Backend",
            "base_url": request.build_absolute_uri('/api/v1/'),
            "endpoints": {
                "auth": {
                    "token": {
                        "url": "/api/v1/auth/token/",
                        "method": "POST",
                        "description": "Xác thực và lấy JWT token",
                        "request": {
                            "username": "string (email của người dùng)",
                            "password": "string"
                        },
                        "response": {
                            "access": "string (JWT token)",
                            "refresh": "string (refresh token)"
                        }
                    },
                    "token_refresh": {
                        "url": "/api/v1/auth/token/refresh/",
                        "method": "POST",
                        "description": "Làm mới JWT token",
                        "request": {
                            "refresh": "string (refresh token)"
                        },
                        "response": {
                            "access": "string (JWT token mới)"
                        }
                    },
                    "logout": {
                        "url": "/api/v1/auth/logout/",
                        "method": "POST",
                        "description": "Đăng xuất (vô hiệu hóa token)",
                        "request": {},
                        "response": {
                            "detail": "string (thông báo thành công)"
                        }
                    }
                },
                "accounts": {
                    "description": "Quản lý tài khoản người dùng",
                    "endpoints": {
                        "register": {
                            "url": "/api/v1/accounts/auth/register/",
                            "method": "POST",
                            "description": "Đăng ký tài khoản mới",
                            "request": {
                                "email": "string (email)",
                                "password": "string",
                                "username": "string (tên người dùng)",
                                "first_name": "string (tùy chọn)",
                                "last_name": "string (tùy chọn)"
                            },
                            "response": {
                                "id": "integer",
                                "email": "string",
                                "username": "string"
                            }
                        },
                        "me": {
                            "url": "/api/v1/accounts/users/me/",
                            "method": "GET",
                            "description": "Lấy thông tin người dùng hiện tại",
                            "request": {},
                            "response": {
                                "id": "integer",
                                "email": "string",
                                "username": "string",
                                "first_name": "string",
                                "last_name": "string",
                                "profile": "object (thông tin profile)"
                            }
                        }
                    }
                },
                "music": {
                    "description": "Quản lý nội dung âm nhạc",
                    "endpoints": {
                        "songs": {
                            "url": "/api/v1/music/songs/",
                            "method": "GET",
                            "description": "Lấy danh sách bài hát",
                            "request": {
                                "genre": "string (lọc theo thể loại, tùy chọn)",
                                "artist": "string (lọc theo nghệ sĩ, tùy chọn)"
                            },
                            "response": {
                                "count": "integer",
                                "next": "string (URL trang kế tiếp)",
                                "previous": "string (URL trang trước)",
                                "results": "array of song objects"
                            }
                        },
                        "playlists": {
                            "url": "/api/v1/music/playlists/",
                            "method": "GET",
                            "description": "Lấy danh sách playlist",
                            "request": {},
                            "response": {
                                "count": "integer",
                                "next": "string (URL trang kế tiếp)",
                                "previous": "string (URL trang trước)",
                                "results": "array of playlist objects"
                            }
                        }
                    }
                },
                "chat": {
                    "description": "Quản lý trò chuyện và tin nhắn",
                    "endpoints": {
                        "conversations": {
                            "url": "/api/v1/chat/conversations/",
                            "method": "GET",
                            "description": "Lấy danh sách cuộc trò chuyện",
                            "request": {},
                            "response": {
                                "count": "integer",
                                "next": "string (URL trang kế tiếp)",
                                "previous": "string (URL trang trước)",
                                "results": "array of conversation objects"
                            }
                        },
                        "messages": {
                            "url": "/api/v1/chat/messages/",
                            "method": "GET",
                            "description": "Lấy tin nhắn trong cuộc trò chuyện",
                            "request": {
                                "conversation_id": "integer (ID cuộc trò chuyện)"
                            },
                            "response": {
                                "count": "integer",
                                "next": "string (URL trang kế tiếp)",
                                "previous": "string (URL trang trước)",
                                "results": "array of message objects"
                            }
                        }
                    }
                },
                "ai": {
                    "description": "AI Assistant API",
                    "endpoints": {
                        "conversations": {
                            "get": {
                                "url": "/api/v1/ai/conversations/",
                                "method": "GET",
                                "description": "Lấy danh sách hội thoại AI của người dùng",
                                "request": {},
                                "response": {
                                    "count": "integer",
                                    "next": "string",
                                    "previous": "string",
                                    "results": "array of conversation objects"
                                }
                            },
                            "post": {
                                "url": "/api/v1/ai/conversations/",
                                "method": "POST",
                                "description": "Tạo hội thoại AI mới",
                                "request": {
                                    "title": "string (tiêu đề hội thoại)",
                                    "system_context": "string (hướng dẫn cho AI)"
                                },
                                "response": {
                                    "id": "integer",
                                    "title": "string",
                                    "user": "object",
                                    "system_context": "string",
                                    "created_at": "datetime",
                                    "updated_at": "datetime",
                                    "messages": "array"
                                }
                            },
                            "detail": {
                                "url": "/api/v1/ai/conversations/{id}/",
                                "method": "GET",
                                "description": "Xem chi tiết hội thoại AI",
                                "request": {},
                                "response": {
                                    "id": "integer",
                                    "title": "string",
                                    "user": "object",
                                    "system_context": "string",
                                    "created_at": "datetime",
                                    "updated_at": "datetime",
                                    "messages": "array of message objects"
                                }
                            },
                            "messages": {
                                "url": "/api/v1/ai/conversations/{id}/messages/",
                                "method": "GET",
                                "description": "Lấy tin nhắn trong hội thoại",
                                "request": {},
                                "response": "array of message objects"
                            },
                            "clear": {
                                "url": "/api/v1/ai/conversations/{id}/clear/",
                                "method": "DELETE",
                                "description": "Xóa tất cả tin nhắn trong hội thoại",
                                "request": {},
                                "response": {}
                            }
                        },
                        "generate_text": {
                            "url": "/api/v1/ai/generate-text/",
                            "method": "POST",
                            "description": "Tạo phản hồi văn bản từ AI",
                            "request": {
                                "prompt": "string (câu hỏi cho AI)",
                                "conversation_id": "integer (tùy chọn)",
                                "system_context": "string (tùy chọn)"
                            },
                            "response": {
                                "response": "string (phản hồi từ AI)",
                                "conversation_id": "integer"
                            }
                        },
                        "generate_multimodal": {
                            "url": "/api/v1/ai/generate-multimodal/",
                            "method": "POST",
                            "description": "Tạo phản hồi từ văn bản + hình ảnh",
                            "request": {
                                "prompt": "string (câu hỏi cho AI)",
                                "image": "file (hình ảnh)",
                                "conversation_id": "integer (tùy chọn)",
                                "system_context": "string (tùy chọn)"
                            },
                            "response": {
                                "response": "string (phản hồi từ AI)",
                                "conversation_id": "integer"
                            }
                        },
                        "system_instructions": {
                            "url": "/api/v1/ai/system-instructions/",
                            "method": "GET",
                            "description": "Lấy danh sách hướng dẫn hệ thống có sẵn",
                            "request": {},
                            "response": {
                                "general": "string",
                                "music": "string",
                                "chat": "string",
                                "playlists": "string",
                                "technical": "string"
                            }
                        },
                        "system_prompts": {
                            "url": "/api/v1/ai/system-prompts/",
                            "method": "GET",
                            "description": "Lấy danh sách prompt hệ thống",
                            "request": {},
                            "response": {
                                "count": "integer",
                                "next": "string",
                                "previous": "string",
                                "results": "array of system prompt objects"
                            }
                        }
                    }
                }
            },
            "websocket": {
                "ai_chat": {
                    "url": "wss://{domain}/ws/ai/chat/{conversation_id}/",
                    "description": "WebSocket cho trò chuyện real-time với AI",
                    "messages": {
                        "send": {
                            "type": "message",
                            "message": "string (nội dung tin nhắn)",
                            "conversation_id": "integer (tùy chọn)",
                            "system_context": "string (tùy chọn)"
                        },
                        "receive": {
                            "type": "message|typing",
                            "message": "string (khi type=message)",
                            "is_typing": "boolean (khi type=typing)",
                            "role": "string (assistant|user)",
                            "conversation_id": "integer",
                            "user_id": "integer"
                        }
                    }
                }
            }
        }
        
        # Nếu yêu cầu format=html, render template
        format_param = request.query_params.get('format', 'json')
        if format_param.lower() == 'html':
            return render(request, 'api_documentation.html', {'api_data': api_documentation})
        
        # Mặc định trả về JSON
        return Response(api_documentation)