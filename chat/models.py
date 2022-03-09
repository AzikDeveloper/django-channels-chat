from chat.base.async_adapters import AsyncModelManager, ModelAsyncMixin
from django.db import models
from .base.utils import generate_session_secret, create_expires_at
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone
from channels.db import database_sync_to_async
from chat.base.utils import BaseUser, get_object_or_not_found


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
    users_ids = models.JSONField(null=True)
    users = models.ManyToManyField(BaseUser, related_name='user_chat', through=Participation)

    def has_user(self, user):
        return user.id in self.users_ids

    @classmethod
    async def has_chat(cls, *users):
        chats = Chat.objects.all()
        for user in users:
            chats = chats.filter(users__in=[user])
        return await database_sync_to_async(chats.exists)()

    async def other_user(self, this_user):
        users = self.users_ids
        users.remove(this_user.id)

        return await get_object_or_not_found(BaseUser, id=users[0])


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


class Notification(models.Model):
    client = models.ForeignKey('chat.ClientSession', related_name='client_action', on_delete=models.CASCADE)
    data = models.JSONField()
