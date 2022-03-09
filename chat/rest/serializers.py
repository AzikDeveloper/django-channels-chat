from chat.models import ClientSession, Chat, Message
from chat.base.async_adapters import AsyncModelSerializer
from rest_framework import serializers
from chat.base.pagination import CursorSetPagination
from django.conf import settings
from django.urls import reverse
from chat.base.utils import BaseUser
from chat.settings import user_fields


class ClientSessionSerializer(AsyncModelSerializer):
    class Meta:
        model = ClientSession
        fields = [
            "user",
            "secret",
            "expires_at",
            "online",
        ]


class MessageSerializer(AsyncModelSerializer):
    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "receiver",
            "chat",
            "text",
            "created_at",
            "edited",
            "seen"
        )
        extra_kwargs = {
            'sender': {
                'required': False,
                'allow_null': True
            }
        }
        read_only_fields = ['created_at', 'edited', 'seen']


class ChatUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUser
        fields = user_fields


class ChatListSerializer(serializers.ModelSerializer):
    next_messages_link = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            "id",
            "user",
            "messages",
            "next_messages_link"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._final_link = None

    def get_messages(self, chat):
        paginator = CursorSetPagination()
        messages = paginator.paginate_queryset(chat.message.all(), self.context.get('request'))
        self.make_next_url(paginator, chat)

        return MessageSerializer(messages, many=True).data

    def make_next_url(self, paginator, chat):
        base_message_pagination_url = settings.HOST + reverse('chat:message-list', args=[chat.id])
        link: str = paginator.get_next_link()
        cursor = link.split('cursor=')[1] if link else ""
        next_link = base_message_pagination_url + '?cursor=' + cursor
        self._final_link = next_link

    def get_next_messages_link(self, chat):
        return self._final_link

    def get_user(self, chat):
        current_user = self.context.get('request').user
        user = chat.users.exclude(user=current_user).first()
        return ChatUserSerializer(user).data


class ChatCreateDetailSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    next_messages_link = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            "id",
            "user",
            "messages",
            "next_messages_link"
        )

    def get_user(self, chat):
        user = self.context.get('user')
        return ChatUserSerializer(user).data

    @staticmethod
    def get_messages(chat):
        return []

    @staticmethod
    def get_next_messages_link(chat):
        return None
