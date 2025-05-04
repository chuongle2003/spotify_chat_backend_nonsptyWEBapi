"""
URL routing for the AI Assistant app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'conversations', views.AIConversationViewSet, basename='ai-conversation')
router.register(r'system-prompts', views.AISystemPromptViewSet, basename='ai-system-prompt')

urlpatterns = [
    # HTML Views
    path('chat/', views.ai_chat_view, name='ai-chat-interface'),
    path('guide/', views.ai_guide_view, name='ai-guide'),
    
    # API Endpoints
    path('', include(router.urls)),
    path('generate-text/', views.AITextRequestView.as_view(), name='generate-text'),
    path('generate-multimodal/', views.AIMultiModalRequestView.as_view(), name='generate-multimodal'),
    path('system-instructions/', views.SystemInstructionsView.as_view(), name='system-instructions'),
    path('api-documentation/', views.APIDocumentationView.as_view(), name='api-documentation'),
] 