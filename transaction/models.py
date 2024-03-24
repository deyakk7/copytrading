from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from trader.models import Trader

User = get_user_model()

USER_DEPOSIT_TYPES = (
    ('deposit', 'DEPOSIT'),
    ('withdraw', 'WITHDRAW'),
)


class Transaction(models.Model):
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    crypto_pair = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=30, decimal_places=7)
    amount = models.DecimalField(max_digits=30, decimal_places=7)
    side = models.BooleanField()


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
