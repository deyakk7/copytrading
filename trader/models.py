import os

from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver


class Trader(models.Model):
    nickname = models.CharField(max_length=50, unique=True)
    about = models.CharField(max_length=500, blank=True)
    date_of_registration = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='trader_photos', blank=True)

    def __str__(self):
        return f"{self.nickname}"

    def save(self, *args, **kwargs):
        if self.pk:
            old_photo = Trader.objects.get(pk=self.pk).photo
            new_photo = self.photo
            if old_photo and old_photo != new_photo:
                if os.path.isfile(old_photo.path):
                    os.remove(old_photo.path)
        super(Trader, self).save(*args, **kwargs)


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


