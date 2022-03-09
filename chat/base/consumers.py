from channels.db import database_sync_to_async
from .main import BaseConsumer
from .dispatch import RequestHandler
from channels.exceptions import StopConsumer
from .utils import BaseUser
from django.conf import settings
from chat.models import ClientSession


class ChatConsumer(BaseConsumer):

    async def connect(self):
        if settings.CHAT_DEBUG:
            client_id = dict(self.scope["headers"])[b"client"].decode("utf8")
            client_session = await database_sync_to_async(
                ClientSession.objects.select_related('user').filter(id=client_id).first
            )()
            await self.perform_authentication(client_session)

        await self.accept()

    async def disconnect(self, close_code):
        # if self.scope['user'].is_authenticated:
        #     await self.channel_layer.group_discard(
        #         self.room_group_name,
        #         self.channel_name
        #     )
        #     await self.change_online(delta=-1)
        raise StopConsumer()

    # async def change_online(self, delta):
    #     user = self.scope["user"]
    #     user.online_count += delta
    #     await database_sync_to_async(user.save)()
    #
    #     if (user.online_count == 0 and delta == -1) or (user.online_count == 1 and delta == 1):
    #         content = {
    #             'action': 'chat__change_online',
    #             'data': {
    #                 'online': bool(user.online_count)
    #             }
    #         }
    #         handler = RequestHandler(content, self)
    #         await handler.handle(internal_request=True)

    async def receive_json(self, content, **kwargs):
        try:
            handler = RequestHandler(content, self)
            await handler.handle(internal_request=False)
        except Exception as error:
            await self.disconnect(500)
            raise error

    async def group_receive(self, event):
        if not (self.channel_name in event.get('exclude')):
            content = event['content']
            await self.send_json(content)

    async def perform_authentication(self, client_session):
        self.scope['user'] = client_session.user
        self.client_session = client_session
        self.room_name = client_session.user.id
        self.room_group_name = 'user_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
