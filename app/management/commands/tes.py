from django.core.management import BaseCommand
from chat.models import Chat
from django.contrib.auth import get_user_model


class Command(BaseCommand):

    def handle(self, *args, **options):
        chat = Chat.objects.first()
        print(chat.users.last())
