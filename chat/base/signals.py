import threading

from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import pre_save
from chat.base.tasks import notification_creator_on_user_update
from chat.models import Participation
from chat.rest.serializers import ChatUserSerializer
from chat.settings import user_fields

BaseUser = get_user_model()


@receiver(pre_save, sender=BaseUser)
def pre_save_user_model(sender, instance, **kwargs):
    if instance.pk is not None:
        user = BaseUser.objects.get(pk=instance.pk)
        changed = False
        for field in user_fields:
            if getattr(user, field) != getattr(instance, field):
                changed = True
                break
        if changed:
            user = instance
            user_data = ChatUserSerializer(user).data

            clients_datas = Participation.objects.filter(chat__users__in=[user]).distinct('user').values_list(
                'user__client_session',
                'user',
                'chat__id',
            )

            data = {
                'action': 'chat__change_profile',
                'type': 'notify',
                'data': {
                    'user': user_data
                }
            }
            thread = threading.Thread(
                target=notification_creator_on_user_update,
                name='create-notification-edit-profile',
                args=[clients_datas, data])
            thread.start()
