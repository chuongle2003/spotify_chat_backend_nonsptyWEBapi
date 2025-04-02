from django.contrib import admin
from .models import Message
# Register your models here.
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')

    list_filter = ('timestamp',)
    ordering = ('id',)