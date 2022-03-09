from channels.layers import get_channel_layer
from chat.models import ClientSession, Notification
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync


async def notification_creator_async(user, data, exclude_client=None):
    clients = ClientSession.objects.filter(user=user)
    if exclude_client:
        clients = clients.exclude(id=exclude_client.id)

    await database_sync_to_async(clients._fetch_all)()

    notifications = []
    for client in clients:
        notifications.append(Notification(client=client, data=data))
    await database_sync_to_async(
        Notification.objects.bulk_create
    )(notifications)


def notification_creator_on_user_update(clients, data):
    layer = get_channel_layer()
    sent_users = []
    notifications = []
    for client in clients:
        client_id, user_id, chat_id = client[0], client[1], client[2]
        data['data']['id'] = chat_id
        notifications.append(
            Notification(client_id=client_id, data=data)
        )
        if user_id not in sent_users:
            async_to_sync(layer.group_send)(
                f'user_{user_id}',
                {
                    'type': 'group.receive',
                    'content': data,
                    'exclude': []
                }
            )
            sent_users.append(user_id)

    Notification.objects.bulk_create(notifications)
