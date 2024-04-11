import os

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Trader(models.Model):
    nickname = models.CharField(max_length=50, unique=True)
    about = models.CharField(max_length=500, blank=True, null=True)
    date_of_registration = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='trader_photos', blank=True, null=True)
    avg_profit_strategies = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_copiers = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    copiers_count = models.IntegerField(default=0)
    visible = models.BooleanField(default=False)

    roi = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    profit_to_loss_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    weekly_trades = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    avg_holding_time = models.CharField(max_length=20, default='No info')
    roi_volatility = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    sortino_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    last_traded_at = models.DateTimeField(default=None, blank=True, null=True)

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

    def get_stats(self):
        return {
            'profit_to_loss_ratio': self.profit_to_loss_ratio,
            'weekly_trades': self.weekly_trades,
            'avg_holding_time': self.avg_holding_time,
            'roi_volatility': self.roi_volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'last_traded_at': self.last_traded_at,
        }
