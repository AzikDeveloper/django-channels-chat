from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class BaseUser(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/')

    @property
    def avatar_url(self):
        return f'{settings.HOST}{self.avatar.url}'
