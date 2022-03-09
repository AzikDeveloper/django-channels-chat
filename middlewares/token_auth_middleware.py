from chat.models import AccessTicket
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware

from .auth_classes import TicketAuth, TokenHeaderAuth


class TokenAuthMiddleware(BaseMiddleware):
    auth_classes = [TicketAuth, TokenHeaderAuth]

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        for each in self.auth_classes:
            await each.authenticate(scope)
            if scope["user"].is_authenticated:
                break
        return await super().__call__(scope, receive, send)
