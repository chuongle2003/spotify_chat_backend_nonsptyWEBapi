"""
Models for the AI Assistant app
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

class AIConversation(models.Model):
    """Model to store AI conversation sessions"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    system_context = models.TextField(blank=True, null=True, 
        help_text="System context/instructions for this conversation")
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.title or 'Conversation'} - {self.user.username}"
        
    def get_conversation_history(self):
        """Get the full conversation history as a list of dictionaries"""
        return list(self.messages.all().order_by('created_at').values('role', 'content'))

class AIMessage(models.Model):
    """Individual messages in an AI conversation"""
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    
    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    has_image = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

class AISystemPrompt(models.Model):
    """Predefined system prompts for different AI use cases"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prompt_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name 