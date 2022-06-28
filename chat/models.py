from chat.base.async_adapters import AsyncModelManager, ModelAsyncMixin
from django.db import models
from .base.utils import generate_session_secret, create_expires_at
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone
from channels.db import database_sync_to_async
from chat.base.utils import BaseUser, get_object_or_not_found


def id_getter(f):
    async def wrapper(self, *args, **kwargs):
        id_list = []
        for arg in args:
            if isinstance(arg, int):
                id_list.append(arg)
            else:
                id_list.append(getattr(arg, "id"))
        return await f(self, *id_list, **kwargs)

    return wrapper


class ClientSession(models.Model, ModelAsyncMixin):
    user = models.ForeignKey(BaseUser, related_name='client_session', on_delete=models.CASCADE)
    secret = models.CharField(max_length=64, default=generate_session_secret)
    expires_at = models.DateTimeField(default=create_expires_at)
    online = models.BooleanField(default=True)

    objects = AsyncModelManager()

    def is_not_expired(self):
        return self.expires_at >= timezone.now()


class Participation(models.Model, ModelAsyncMixin):
    user = models.ForeignKey(BaseUser, related_name='user_participation', on_delete=models.SET_NULL, null=True)
    chat = models.ForeignKey('chat.Chat', related_name='chat_participation', on_delete=models.CASCADE)


class Chat(models.Model, ModelAsyncMixin):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    users = models.ManyToManyField(BaseUser, related_name='user_chat', through=Participation)

    def __str__(self):
        return " | ".join(list(self.users.values_list("username", flat=True)))

    @id_getter
    async def has_user(self, user_id):
        return await database_sync_to_async(
            self.users.filter(id=user_id).exists
        )()

    @classmethod
    async def has_chat(cls, user1_id, user2_id):
        chats = Chat.objects.all()
        for user in (user1_id, user2_id):
            chats = chats.filter(users__in=[user])
        return await database_sync_to_async(chats.exists)()

    async def other_user(self, this_user_id):
        return await database_sync_to_async(
            self.users.exclude(id=this_user_id).first
        )()


class Ban(models.Model):
    chat = models.ForeignKey('chat.Chat', related_name='chat_ban', on_delete=models.CASCADE)
    user = models.ForeignKey(BaseUser, related_name='user_ban', on_delete=models.SET_NULL, null=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)


class Message(models.Model, ModelAsyncMixin):
    sender = models.ForeignKey(BaseUser, related_name='sent_message', on_delete=models.SET_NULL, null=True)
    receiver = models.ForeignKey(BaseUser, related_name='received_message', on_delete=models.SET_NULL, null=True)
    chat = models.ForeignKey('chat.Chat', related_name='chat_message', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    edited = models.BooleanField(default=False, blank=True)
    seen = models.BooleanField(default=False, blank=True)


@receiver(pre_save, sender=Message)
def set_message_edited(sender: Message, instance: Message, **kwargs):
    if instance.pk is not None:
        message = Message.objects.get(id=instance.id)
        if message.text != instance.text:
            instance.edited = True
