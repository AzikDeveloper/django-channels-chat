from factory import Factory, Faker
from django.contrib.auth import get_user_model


class UserFactory(Factory):
    username = Faker('email')
    password = '12341234'
    first_name = Faker('first_name')
    last_name = Faker('last_name')

    class Meta:
        model = get_user_model()
