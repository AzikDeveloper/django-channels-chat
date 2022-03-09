from rest_framework import generics
from chat.models import Chat, Message
from chat.rest import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from chat.base.pagination import CursorSetPagination


class ChatListView(generics.ListAPIView):
    queryset = Chat.objects.all()
    serializer_class = serializers.ChatListSerializer
    permission_classes = [IsAuthenticated]

    def filter_queryset(self, queryset):
        return self.queryset.filter(users__in=[self.request.user]).distinct()


class MessageListView(generics.ListAPIView):
    queryset = Message.objects.all()
    serializer_class = serializers.MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CursorSetPagination

    def filter_queryset(self, queryset):
        chat = generics.get_object_or_404(Chat, id=self.kwargs.get('pk'))
        if chat.has_user(self.request.user):
            return queryset.filter(chat=chat)
        else:
            raise PermissionDenied()
