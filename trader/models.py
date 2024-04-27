import os
import uuid

from dicebear import DAvatar, DStyle, DFormat
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()

TRADER_TYPES = (
    ("Conservative", "conservative"),
    ("Trending", "trending"),
)


class Trader(models.Model):
    nickname = models.CharField(max_length=50, unique=True)
    about = models.CharField(max_length=500, blank=True, null=True)
    date_of_registration = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='trader_photos', blank=True, null=True)
    avg_profit_strategies = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_copiers = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    copiers_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    visible = models.BooleanField(default=False)
    deposit = models.DecimalField(max_digits=30, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    available_deposit = models.DecimalField(max_digits=30, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    trader_type = models.CharField(max_length=30, default=None, null=True, blank=True, choices=TRADER_TYPES)

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

    @staticmethod
    def generate_avatar():
        unique_name = str(uuid.uuid4())
        path = f'trader_photos/{unique_name}.png'

        av = DAvatar(
            style=DStyle.identicon,
            seed=f"{unique_name}",
        )
        av.save(
            location=f"{settings.MEDIA_ROOT}/trader_photos/",
            file_name=unique_name,
            file_format=DFormat.png
        )
        return path

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if not self.photo:
            self.photo = self.generate_avatar()

        if self.pk:
            old_photo = Trader.objects.get(pk=self.pk).photo
            new_photo = self.photo
            if old_photo and old_photo != new_photo:
                if os.path.isfile(old_photo.path):
                    os.remove(old_photo.path)
        super(Trader, self).save(*args, **kwargs)

        if is_new:
            TraderProfitHistory.objects.create(trader=self, value=0)

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

    def get_chart_stats(self):
        pass


class TraderProfitHistory(models.Model):
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='profits')
    value = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    date = models.DateTimeField(auto_now_add=True)
