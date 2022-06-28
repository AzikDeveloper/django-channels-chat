from django.contrib import admin
from .models import *
from django.contrib.admin import ModelAdmin
from chat.base.setup import CHAT_DEBUG


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
    if CHAT_DEBUG:
        list_display += ["secret"]
    list_display += ["id"]

    readonly_fields = ["secret"]


@admin.register(Participation)
class ParticipationAdmin(ModelAdmin):
    list_display = ["user", "chat"]
    search_fields = ["user"]


class ParticipationTabular(admin.TabularInline):
    model = Participation
    extra = 0


@admin.register(Chat)
class ChatAdmin(ModelAdmin):
    inlines = [ParticipationTabular]
