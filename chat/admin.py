from django.contrib import admin
from .models import *
from django.contrib.admin import ModelAdmin
from django.conf import settings


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = [
        "text",
        "sender",
        "receiver",
        "chat_id",
        "created_at",
        "edited",
        "seen",
        "id"
    ]


@admin.register(ClientSession)
class ClientSessionAdmin(ModelAdmin):
    list_display = ["user", "expires_at"]
    if settings.DEBUG:
        list_display += ["secret"]
    list_display += ["id"]

    readonly_fields = ["secret"]


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ["get_client", "data", "id"]
    readonly_fields = [] if settings.CHAT_DEBUG else ["data"]

    @admin.display(ordering='client__user', description='User')
    def get_client(self, obj: Notification):
        return obj.client.user


@admin.register(Chat)
class ChatAdmin(ModelAdmin):
    pass
