from django.core.management import BaseCommand
from app.factory import UserFactory
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('count')

    def handle(self, *args, **options):
        users = []
        for i in range(int(options['count'])):
            users.append(UserFactory())
        get_user_model().objects.bulk_create(users)
