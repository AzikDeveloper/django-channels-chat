from rest_framework import generics
from rest_framework.views import APIView
from chat.models import Chat, Message, ClientSession, Participation
from chat.rest import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from chat.base.pagination import CursorSetPagination
from rest_framework.generics import get_object_or_404
from django.db.models import Max, F, Q, Count, Subquery, OuterRef
from django.db import models as db_models
from chat.base.setup import CHAT_USER_FIELDS
from rest_framework.exceptions import ValidationError
from datetime import datetime
from rest_framework.response import Response


class ChatListView(generics.ListAPIView):
    queryset = Chat.objects.prefetch_related('users')

    serializer_class = serializers.ChatListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        last_message = Message.objects.filter(Q(chat_id=OuterRef('id'))).order_by(
            '-created_at')[:1]
        user = Participation.objects.filter(~Q(chat=OuterRef('id')) & ~Q(user=self.request.user))[:1]

        user_annotation = {
            f'user_{field}': Subquery(user.values(f'user__{field}'), output_field=field_type())
            for field, field_type in CHAT_USER_FIELDS.items()
        }

        return self.queryset.annotate(
            last_message_text=Subquery(last_message.values('text'), output_field=db_models.CharField()),
            last_message_sender=Subquery(last_message.values('sender'), output_field=db_models.IntegerField()),
            last_message_seen=Subquery(last_message.values('seen'), output_field=db_models.BooleanField()),
            unseen_messages_count=Count(
                'chat_message__text',
                filter=Q(chat_message__seen=False) & ~Q(chat_message__sender=self.request.user)
            ),
            **user_annotation
        )

    def filter_queryset(self, queryset):
        return queryset.filter(users__in=[self.request.user])


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
