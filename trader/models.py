import os

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Trader(models.Model):
    nickname = models.CharField(max_length=50, unique=True)
    about = models.CharField(max_length=500, blank=True)
    date_of_registration = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='trader_photos', blank=True)
    avg_profit_strategies = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    followers_count = models.IntegerField(default=0)
    copiers_count = models.IntegerField(default=0)

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


class UsersFollowsTrader(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_traders')
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='followers')
    date_of_following = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trader',)

    def __str__(self):
        return f"{self.user} follows {self.trader}"
