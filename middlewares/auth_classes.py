from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.utils import timezone
from django.conf import settings
from chat.base.utils import BaseUser


class TicketAuth:
    @classmethod
    async def authenticate(cls, scope):
        try:
            token_key = (dict((x.split('=') for x in scope['query_string'].decode().split("&")))).get('ticket', None)
        except ValueError:
            token_key = None
        scope['user'] = AnonymousUser() if token_key is None else await cls.get_user(token_key)

    @classmethod
    @database_sync_to_async
    def get_user(cls, secret):
        try:
            ticket = AccessTicket.objects.select_related('user__worker', 'user__company').get(
                secret=secret,
                expires_at__gte=timezone.now()
            )
        except AccessTicket.DoesNotExist:
            return AnonymousUser()
        else:
            return ticket.user
        finally:
            AccessTicket.objects.filter(expires_at__lt=timezone.now()).delete()


class TokenHeaderAuth:
    @classmethod
    async def authenticate(cls, scope):
        try:
            token = dict(scope["headers"])[b"token"].decode("utf8")
            UntypedToken(token)
        except (InvalidToken, TokenError, KeyError):
            return
        else:
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = await cls.get_user(decoded_data["user_id"])
            scope["user"] = user

    @classmethod
    async def get_user(cls, user_id):
        try:
            user = await database_sync_to_async(BaseUser.objects.select_related('worker', 'company').get)(
                id=user_id
            )
        except BaseUser.DoesNotExist:
            return AnonymousUser()
        else:
            return user
