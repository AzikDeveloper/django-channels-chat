from chat.handler_routing import handlers
from .exceptions import *
from .utils import WRequest, Notify
import traceback

EXCEPTIONS = (NotFound, PermissionDenied, ValidationError,)


class RequestHandler:
    def __init__(self, content, consumer):
        self.request = WRequest(content, consumer.scope["user"])
        self.consumer = consumer

    async def handle(self, internal_request=False):
        try:
            if self.request.action not in handlers.keys():
                await self.fail_handler("action name is not valid!")
                return

            handler = handlers[self.request.action]

            if not (internal_request or (not internal_request and not handler.internal)):
                await self.fail_handler(PermissionDenied.default_message)
                return
            try:
                await handler(self.request, self.consumer).handle()
            except EXCEPTIONS as e:
                await self.fail_handler(e.message)
        except Exception as e:
            print(traceback.format_exc())
            await self.fail_handler(e)

    async def fail_handler(self, detail):
        notify = Notify(self.request.action, {'detail': detail})
        await self.consumer.send_json(notify.as_fail_response)
