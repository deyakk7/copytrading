import os

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Trader(models.Model):
    nickname = models.CharField(max_length=50, unique=True)
    about = models.CharField(max_length=500, blank=True)
    date_of_registration = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='trader_photos', blank=True)
    avg_profit_strategies = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    copiers_count = models.IntegerField(default=0)

    profit_to_loss_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    weekly_trades = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    avg_holding_time = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    roi_volatility = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    sortino_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    last_traded_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

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
