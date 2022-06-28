from channels.db import database_sync_to_async
from .main import BaseConsumer
from .dispatch import RequestHandler
from channels.exceptions import StopConsumer
from chat.base.setup import CHAT_DEBUG
from chat.models import ClientSession
from chat.models import Participation
from .utils import count_query, debug_request


class ChatConsumer(BaseConsumer):

    @count_query
    async def connect(self):
        if CHAT_DEBUG:
            client_id = dict(self.scope["headers"])[b"client"].decode("utf8")
            client_session = await database_sync_to_async(
                ClientSession.objects.select_related('user').filter(id=client_id).first
            )()
            await self.perform_authentication(client_session)
        await self.accept()

    @count_query
    async def disconnect(self, close_code):
        if self.scope['user'].is_authenticated:
            self.client_session.online = False
            await self.client_session.save_async()

            online_clients = await database_sync_to_async(
                ClientSession.objects.filter(user=self.scope['user'], online=True).exists
            )()
            if not online_clients:
                await self.change_online(False)

        raise StopConsumer()

    @debug_request
    @count_query
    async def receive_json(self, content, **kwargs):
        try:
            handler = RequestHandler(content, self)
            await handler.handle(internal_request=False)
        except Exception as error:
            await self.disconnect(500)
            raise error

    async def group_receive(self, event):
        if not (self.client_session.id in event.get('exclude_clients')):
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

        online_clients = await database_sync_to_async(
            ClientSession.objects.filter(user=self.scope['user'], online=True).exists
        )()
        if not online_clients:
            await self.change_online(True)

    async def change_online(self, is_online):
        self.scope['user'].online = is_online
        await database_sync_to_async(
            self.scope['user'].save
        )()

        clients_datas = await database_sync_to_async(
            Participation.objects.filter(chat__users__in=[self.scope['user']]).distinct('user').values_list
        )('user', 'chat__id', )
        await database_sync_to_async(
            clients_datas._fetch_all
        )()

        sent_users = []
        for client_data in clients_datas:
            user_id, chat_id = client_data[0], client_data[1]
            data = {
                'action': 'chat__change_online',
                'type': 'notify',
                'data': {
                    'id': chat_id,
                    'online': is_online
                }
            }
            if user_id not in sent_users and user_id != self.scope['user'].id:
                await self.channel_layer.group_send(
                    f'user_{user_id}',
                    {
                        'type': 'group.receive',
                        'content': data,
                        'exclude_clients': [self.client_session.id]
                    }
                )
                sent_users.append(user_id)
