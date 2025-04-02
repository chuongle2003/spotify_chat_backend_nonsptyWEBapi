from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Message
from .serializers import MessageSerializer, ConversationSerializer
from django.db.models import Q

# Create your views here.

class MessageListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).order_by('-timestamp')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        )

class ConversationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).order_by('-timestamp').distinct('sender', 'receiver')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class ConversationDetailView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        other_user_id = self.kwargs['user_id']
        return Message.objects.filter(
            (Q(sender=user) & Q(receiver_id=other_user_id)) |
            (Q(receiver=user) & Q(sender_id=other_user_id))
        ).order_by('timestamp')
