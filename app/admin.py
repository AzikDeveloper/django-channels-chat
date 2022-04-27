from django.contrib import admin
from .models import (
    BaseUser
)
from chat.models import (
    Participation,
    Chat
)
from django.contrib.auth.admin import UserAdmin


class ParticipationTabular(admin.TabularInline):
    model = Participation


@admin.register(BaseUser)
class UserAdmin(UserAdmin):
    inlines = [ParticipationTabular]
