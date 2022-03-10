from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class BaseUser(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    online = models.BooleanField(default=False)

    @property
    def avatar_url(self):
        return f'{settings.HOST}{self.avatar.url}' if self.avatar else ""
