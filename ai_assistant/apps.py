"""
App configuration for AI Assistant
"""
from django.apps import AppConfig

class AIAssistantConfig(AppConfig):
    """Configuration for the AI Assistant app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_assistant'
    verbose_name = 'AI Assistant'
    
    def ready(self):
        """Perform initialization when app is ready"""
        pass 