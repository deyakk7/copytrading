from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from strategy.models import Strategy
from trader.models import Trader

User = get_user_model()

USER_DEPOSIT_TYPES = (
    ('deposit', 'DEPOSIT'),
    ('withdraw', 'WITHDRAW'),
)

TRANSACTION_SIDE_TYPES = (
    ('short', 'long'),
    ('long', 'long'),
)


class TransactionClose(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    crypto_pair = models.CharField(max_length=10)
    total_value = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    side = models.CharField(max_length=10, choices=TRANSACTION_SIDE_TYPES, default='long')
    open_price = models.DecimalField(max_digits=30, decimal_places=7, default=0)
    close_price = models.DecimalField(max_digits=30, decimal_places=7, default=0)
    close_time = models.DateTimeField(default=timezone.now)
    roi = models.DecimalField(max_digits=30, decimal_places=7, default=0)

    def __str__(self):
        return f'{self.strategy} - {self.crypto_pair} - {self.side} - {self.roi} - {self.close_time}'


class TransactionOpen(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    crypto_pair = models.CharField(max_length=10)
    side = models.CharField(max_length=10, choices=TRANSACTION_SIDE_TYPES, default='long')
    open_price = models.DecimalField(max_digits=30, decimal_places=7, default=0)
    total_value = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    open_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.strategy} - {self.crypto_pair} - {self.side} - {self.open_time}'


class Transfer(models.Model):
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=30, decimal_places=2)
    time = models.DateTimeField(default=timezone.now)
    side = models.BooleanField()


class UserDeposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=30, decimal_places=2)
    time = models.DateTimeField(default=timezone.now)
    side = models.CharField(choices=USER_DEPOSIT_TYPES, max_length=10)
