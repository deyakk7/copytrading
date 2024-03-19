import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from trader.models import Trader


@receiver(post_delete, sender=Trader)
def photo_post_delete_handler(sender, **kwargs):
    instance = kwargs['instance']
    if instance.photo:
        if os.path.isfile(instance.photo.path):
            os.remove(instance.photo.path)


@receiver(pre_save, sender=Trader)
def photo_pre_save_handler(sender, instance, **kwargs):
    if instance.pk:
        old_photo = Trader.objects.get(pk=instance.pk).photo
        new_photo = instance.photo
        if old_photo and old_photo != new_photo:
            if os.path.isfile(old_photo.path):
                os.remove(old_photo.path)

