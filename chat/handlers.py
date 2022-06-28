from chat.base.main import BaseHandler
from chat.rest.serializers import ClientSessionSerializer, ChatCreateDetailSerializer, MessageSerializer
from chat.base.async_adapters import authenticate_async
from chat.models import ClientSession
from chat.base import status
from chat.base.exceptions import ValidationError
from chat.base.utils import BaseUser, get_object_or_not_found
from chat.models import Participation, Chat, Message


class CreateClientSessionHandler(BaseHandler):
    authentication_required = False

    async def main(self, request) -> None:
        username: str = request.data.get('username')
        password: str = request.data.get('password')
        user: BaseUser = await authenticate_async(username=username, password=password)
        if user is not None:
            serializer = ClientSessionSerializer(data={'user': user.id})
            await serializer.is_valid_async(raise_exception=True)
            client_session: ClientSession = await serializer.save_async()

            await self.consumer.perform_authentication(client_session)
            await self.respond(data=serializer.data)
        else:
            raise ValidationError("Incorrect authentication credentials!")


class AuthorizationHandler(BaseHandler):
    authentication_required = False

    async def main(self, request) -> None:
        client_session: ClientSession = await get_object_or_not_found(
            ClientSession, select_related=["user"],
            secret=request.data.get("secret")
        )
        if client_session.is_not_expired():
            await self.consumer.perform_authentication(client_session)
            await self.respond(status=status.SUCCESS_RESPONSE)
        else:
            await client_session.delete_async()
            await self.respond(status=status.FAIL_RESPONSE)


class ChatCreateHandler(BaseHandler):
    queryset = BaseUser.objects.prefetch_related('client_session')
    lookup_kwarg = 'user'

    async def main(self, request) -> None:
        user: BaseUser = await self.get_object()

        chat: Chat = await Chat.create_async(users_ids=[user.id, request.user.id])
        await Participation.create_async(user=self.request.user, chat=chat)
        await Participation.create_async(user=user, chat=chat)

        chat_data1: dict = ChatCreateDetailSerializer(chat, context={'user': user}).data
        chat_data2: dict = ChatCreateDetailSerializer(chat, context={'user': request.user}).data

        await self.respond(chat_data1, status.SUCCESS_RESPONSE)
        await self.send(user, chat_data2)
        await self.send(request.user, chat_data1, exclude_current=True)

    async def check_permissions(self) -> bool:
        user: BaseUser = await self.get_object()
        return not await Chat.has_chat(self.request.user.id, user.id)


class MessageSendHandler(BaseHandler):
    queryset = Chat.objects.all()
    lookup_kwarg = 'chat'

    async def main(self, request) -> None:
        serializer = MessageSerializer(data=request.data)
        await serializer.is_valid_async(raise_exception=True)

        chat: Chat = await self.get_object()
        receiver: BaseUser = await chat.other_user(request.user.id)
        await serializer.save_async(sender=request.user, receiver=receiver)

        await self.respond(serializer.data)
        await self.send(receiver.id, serializer.data)
        await self.send(request.user.id, serializer.data, exclude_current=True)

    async def check_permissions(self) -> bool:
        chat: Chat = await self.get_object()
        return await chat.has_user(self.request.user.id)


class MessageSeeHandler(BaseHandler):
    queryset = Message.objects.select_related('sender', 'receiver')

    async def main(self, request):
        message: Message = await self.get_object()
        if message.seen:
            raise ValidationError('This message is already seen!')

        message.seen = True
        await message.save_async()

        data = {'id': message.id}
        await self.respond(data, status.SUCCESS_RESPONSE)
        await self.send(message.sender, data)
        await self.send(message.receiver, data, exclude_current=True)

    async def check_permissions(self) -> bool:
        message: Message = await self.get_object()
        return message.receiver == self.request.user


class MessageEditHandler(BaseHandler):
    queryset = Message.objects.select_related('sender', 'receiver')

    async def main(self, request) -> None:
        message: Message = await self.get_object()
        message.text = request.data.get('text')
        await message.save_async()

        data = {'id': message.id, 'text': message.text, 'edited': message.edited}
        await self.respond(data)
        await self.send(message.receiver, data)
        await self.send(message.sender, data, exclude_current=True)

    async def check_permissions(self) -> bool:
        message: Message = await self.get_object()
        return message.sender == self.request.user


class MessageDeleteHandler(BaseHandler):
    queryset = Message.objects.select_related('sender', 'receiver')

    async def main(self, request) -> None:
        message: Message = await self.get_object()
        message_id, receiver, sender = message.id, message.receiver, message.sender

        await message.delete_async()
        data = {'id': message_id}

        await self.respond(data)
        await self.send(receiver, data, exclude_current=request.user == receiver)
        await self.send(sender, data, exclude_current=request.user == sender)

    async def check_permissions(self) -> bool:
        message: Message = await self.get_object()
        return self.request.user in (message.sender, message.receiver)


class ChatDeleteHandler(BaseHandler):
    queryset = Chat.objects.prefetch_related('users')

    async def main(self, request):
        chat: Chat = await self.get_object()
        chat_id, chat_users = chat.id, chat.users.all()
        await chat.delete_async()

        data = {'id': chat_id}

        await self.respond(data)
        for chat_user in chat_users:
            await self.send(chat_user, data, exclude_current=chat_user == request.user)

    async def check_permissions(self) -> bool:
        chat: Chat = await self.get_object()
        return await chat.has_user(self.request.user.id)


class AboutMeHandler(BaseHandler):
    authentication_required = False

    async def main(self, request) -> None:
        data = {'user': str(request.user)}
        return await self.respond(data)
