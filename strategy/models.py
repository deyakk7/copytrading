from django.contrib.auth import get_user_model
from django.db import models

from trader.models import Trader

User = get_user_model()


class Strategy(models.Model):
    name = models.CharField(max_length=100)
    avg_profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    about = models.TextField()
    total_deposited = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    min_deposit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    max_deposit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='strategies', null=True, blank=True)

    def __str__(self):
        return self.name


class UsersInStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='users')
    value = models.DecimalField(default=0, decimal_places=7, max_digits=30)
