import secrets
import traceback
from channels.exceptions import StopConsumer
from django.core.exceptions import ObjectDoesNotExist
from .exceptions import NotFound
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

BaseUser: User = get_user_model()


@database_sync_to_async
def get_object_or_not_found(model_klass, **filter_kwargs):
    try:
        return model_klass.objects.get(**filter_kwargs)
    except ObjectDoesNotExist as e:
        raise NotFound(e)


def create_expires_at():
    return timezone.now() + timezone.timedelta(days=settings.CHAT_USER_SESSION_EXPIRATION)


def catch_exception(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except StopConsumer:
            raise
        except Exception as e:
            print(traceback.format_exc().strip('\n'), '<--- from consumer')
            raise

    return wrapper


class Notify:
    def __init__(self, action=None, data=None):
        if data is None:
            data = {}
        self.action = action
        self.data = data

    @property
    def as_notify(self):
        return {
            'action': self.action,
            'type': 'notify',
            'data': self.data
        }

    @property
    def as_success_response(self):
        return {
            'action': self.action,
            'type': 'response',
            'status': 'success',
            'data': self.data
        }

    @property
    def as_fail_response(self):
        return {
            'action': self.action,
            'type': 'response',
            'status': 'fail',
            'data': self.data
        }

    def __str__(self):
        return f'{self.action}, {self.data}'


class WRequest:
    def __init__(self, content, user):
        self.user = user
        self.action = content.get('action')
        self.data = content.get('data')


def generate_session_secret():
    return secrets.token_urlsafe(32)
