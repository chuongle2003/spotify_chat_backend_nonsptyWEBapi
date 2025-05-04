"""
Admin configuration for AI Assistant app
"""
from django.contrib import admin
from .models import AIConversation, AIMessage, AISystemPrompt

class AIMessageInline(admin.TabularInline):
    """Inline display of messages in a conversation"""
    model = AIMessage
    readonly_fields = ('created_at',)
    extra = 0
    
    def has_add_permission(self, request, obj=None):
        """Disable adding messages through the admin"""
        return False

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    """Admin interface for AI Conversations"""
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AIMessageInline]

@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    """Admin interface for AI Messages"""
    list_display = ('conversation', 'role', 'short_content', 'created_at', 'has_image')
    list_filter = ('role', 'created_at', 'has_image')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('created_at',)
    
    def short_content(self, obj):
        """Display a shortened version of the message content"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    
    short_content.short_description = 'Content'

@admin.register(AISystemPrompt)
class AISystemPromptAdmin(admin.ModelAdmin):
    """Admin interface for System Prompts"""
    list_display = ('name', 'short_description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description', 'prompt_text')
    readonly_fields = ('created_at', 'updated_at')
    
    def short_description(self, obj):
        """Display a shortened version of the description"""
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    
    short_description.short_description = 'Description' 