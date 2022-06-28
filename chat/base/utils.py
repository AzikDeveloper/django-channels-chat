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
from django.db import connections
import json

BaseUser: User = get_user_model()


async def get_object_or_not_found(model_klass, select_related: list = None, **filter_kwargs):
    try:
        if select_related is not None:
            return await database_sync_to_async(
                model_klass.objects.select_related(*select_related).get
            )(**filter_kwargs)
        else:
            return await database_sync_to_async(
                model_klass.objects.get
            )(**filter_kwargs)

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


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def count_query(func):
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        total_queries_count = sum(len(c.queries) for c in connections.all())
        print(Bcolors.OKBLUE + f"scope: {func.__name__}")
        print(Bcolors.OKBLUE + str(total_queries_count) + Bcolors.ENDC)
        return result

    return wrapper


def debug_request(receiver_func):
    async def wrapper(*args, **kwargs):
        print(Bcolors.OKGREEN, "-" * 45, Bcolors.ENDC)
        print(Bcolors.BOLD, Bcolors.OKGREEN, json.dumps(args[1], indent=4), Bcolors.ENDC)
        print(Bcolors.OKGREEN, "-" * 45, Bcolors.ENDC)
        result = await receiver_func(*args, **kwargs)
        return result

    return wrapper
