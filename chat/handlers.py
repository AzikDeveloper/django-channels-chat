from chat.base.main import BaseHandler
from chat.rest.serializers import ClientSessionSerializer, ChatCreateDetailSerializer, MessageSerializer
from chat.base.async_adapters import authenticate
from chat.models import ClientSession
from chat.base import status
from channels.db import database_sync_to_async
from chat.base.exceptions import ValidationError
from chat.base.utils import BaseUser, get_object_or_not_found
from chat.models import Participation, Chat, Message


class CreateClientSessionHandler(BaseHandler):
    authentication_required = False

    async def main(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = await authenticate(username=username, password=password)
        if user is not None:
            serializer = ClientSessionSerializer(data={'user': user.id})
            await serializer.is_valid_async(raise_exception=True)
            client_session = await serializer.save_async()

            await self.consumer.perform_authentication(client_session)
            await self.respond(data=serializer.data, status=status.SUCCESS_RESPONSE)
        else:
            raise ValidationError("Incorrect authentication credentials!")


class AuthorizationHandler(BaseHandler):
    authentication_required = False
    queryset = ClientSession.objects.select_related('user')
    lookup_field = "secret"
    lookup_kwarg = "secret"

    async def main(self, request):
        client_session = await self.get_object()
        if client_session.is_not_expired():
            await self.consumer.perform_authentication(client_session)
            await self.respond(status=status.SUCCESS_RESPONSE)
        else:
            await client_session.delete_async()
            await self.respond(status=status.FAIL_RESPONSE)


class ChatCreateHandler(BaseHandler):
    queryset = BaseUser.objects.prefetch_related('client_session')
    lookup_kwarg = 'user'

    async def main(self, request):
        user = await self.get_object()
        if await Chat.has_chat(request.user, user):
            raise ValidationError("You have already chat with this user")
        else:
            chat = await database_sync_to_async(
                Chat.objects.create
            )(users_ids=[user.id, request.user.id])

            await database_sync_to_async(
                Participation.objects.create
            )(user=self.request.user, chat=chat)
            await database_sync_to_async(
                Participation.objects.create
            )(user=user, chat=chat)

            chat_data1 = ChatCreateDetailSerializer(chat, context={'user': user}).data
            chat_data2 = ChatCreateDetailSerializer(chat, context={'user': request.user}).data
            await self.respond(chat_data1, status.SUCCESS_RESPONSE)
            await self.send(user, chat_data2)
            await self.send(request.user, chat_data1, exclude_current=True)


class MessageSendHandler(BaseHandler):
    queryset = Chat.objects.all()
    lookup_kwarg = 'chat'

    async def main(self, request):
        serializer = MessageSerializer(data=request.data)
        await serializer.is_valid_async(raise_exception=True)

        chat = await self.get_object()
        receiver = await chat.other_user(this_user=request.user)
        await serializer.save_async(sender=request.user, receiver=receiver)

        await self.respond(serializer.data)
        await self.send(receiver, serializer.data)
        await self.send(request.user, serializer.data, exclude_current=True)

    async def check_permissions(self):
        chat = await self.get_object()
        return chat.has_user(self.request.user)


class MessageSeeHandler(BaseHandler):
    queryset = Message.objects.select_related('sender', 'receiver')

    async def main(self, request):
        message = await self.get_object()
        if message.seen:
            raise ValidationError('This message is already seen!')

        message.seen = True
        await database_sync_to_async(message.save)()

        data = {'id': message.id}
        await self.respond(data, status.SUCCESS_RESPONSE)
        await self.send(message.sender, data)
        await self.send(message.receiver, data, exclude_current=True)

    async def check_permissions(self):
        message = await self.get_object()
        return message.receiver == self.request.user


class MessageEditHandler(BaseHandler):
    queryset = Message.objects.select_related('sender', 'receiver')

    async def main(self, request):
        message = await self.get_object()
        message.text = request.data.get('text')
        await database_sync_to_async(message.save)()

        data = {'id': message.id, 'text': message.text, 'edited': message.edited}
        await self.respond(data, status.SUCCESS_RESPONSE)
        await self.send(message.receiver, data)
        await self.send(message.sender, data, exclude_current=True)

    async def check_permissions(self):
        message = await self.get_object()
        return message.sender == self.request.user


class MessageDeleteHandler(BaseHandler):
    queryset = Message.objects.select_related('sender', 'receiver')

    async def main(self, request):
        message = await self.get_object()
        message_id, receiver, sender = message.id, message.receiver, message.sender

        await database_sync_to_async(message.delete)()
        data = {'id': message_id}

        await self.respond(data, status.SUCCESS_RESPONSE)
        await self.send(receiver, data, exclude_current=request.user == receiver)
        await self.send(sender, data, exclude_current=request.user == sender)

    async def check_permissions(self):
        message = await self.get_object()
        return self.request.user in [message.sender, message.receiver]


class ChatDeleteHandler(BaseHandler):
    queryset = Chat.objects.prefetch_related('users')

    async def main(self, request):
        chat = await self.get_object()
        chat_id, chat_users = chat.id, chat.users.all()
        await database_sync_to_async(chat.delete)()

        data = {'id': chat_id}
        await self.respond(data, status.SUCCESS_RESPONSE)
        for chat_user in chat_users:
            await self.send(chat_user, data, exclude_current=chat_user == request.user)

    async def check_permissions(self):
        chat = await self.get_object()
        return chat.has_user(self.request.user)
