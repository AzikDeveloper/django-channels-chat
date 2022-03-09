from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        import chat.base.signals
        from chat.base.utils import BaseUser
        from chat.models import ClientSession

        BaseUser.objects.update(online=False)
        ClientSession.objects.update(online=False)
