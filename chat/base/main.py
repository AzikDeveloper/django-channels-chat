import asyncio

from .utils import catch_exception
import inspect
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from .exceptions import NotFound
from .exceptions import PermissionDenied
from channels.db import database_sync_to_async
from chat.base import status as _status
from chat.base.tasks import notification_creator_async


class BaseConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = 'unauthorized'
        self.room_group_name = 'unauthorized_group'
        self.client_session = None

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)
        if inspect.ismethod(value):
            return catch_exception(value)
        return value


class BaseHandler:
    queryset = None
    """
        You should specify select_related and prefetch_related if you want use the relational fields.
        If you dont do it, then it makes a synchronous call to the db.
    """
    lookup_field = 'id'
    lookup_kwarg = 'id'
    internal = False
    authentication_required = True

    def __init__(self, request, consumer):
        self._model_object = None
        self.request = request
        self.consumer = consumer

    async def handle(self):
        permission = await self.check_permissions()
        if not permission:
            raise PermissionDenied()

        if self.authentication_required:
            if not self.consumer.scope['user'].is_authenticated:
                raise PermissionDenied("Authentication required!")

        await self.main(self.request)

    async def main(self, request):
        assert True, (
            "main() must be implemented"
        )

    async def check_permissions(self):
        """should be implemented"""
        return True

    async def get_object(self, cached=True):
        try:
            if cached and self._model_object:
                return self._model_object
            else:
                search_lookup = {self.lookup_field: self.request.data.get(self.lookup_kwarg)}
                self._model_object = await database_sync_to_async(self.queryset.get)(**search_lookup)
                return self._model_object
        except ObjectDoesNotExist as e:
            raise NotFound(e)

    async def respond(self, data=None, status=None):
        if data is None:
            data = {}

        result_data = {
            'action': self.request.action
        }
        if status == _status.SUCCESS_RESPONSE:
            result_data['type'] = 'response'
            result_data['status'] = 'success'
        elif status == _status.FAIL_RESPONSE:
            result_data['type'] = 'response'
            result_data['status'] = 'fail'
        elif status == _status.NOTIFY:
            result_data['type'] = 'notify'

        result_data['data'] = data
        await self.consumer.send_json(result_data)

    async def create_notifications(self, user, data, exclude_current):
        asyncio.get_event_loop().create_task(
            notification_creator_async(user, data, self.consumer.client_session if exclude_current else None)
        )

    async def send(self, user, data, exclude=None, exclude_current=False):
        if exclude is None:
            exclude = []

        if exclude_current:
            exclude += [self.consumer.channel_name]

        content = {
            'action': self.request.action,
            'type': _status.NOTIFY,
            'data': data
        }
        await self.consumer.channel_layer.group_send(
            f'user_{user.id}',
            {
                'type': 'group.receive',
                'content': content,
                'exclude': exclude
            }
        )
        await self.create_notifications(user, content, exclude_current)
