from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from trader.models import Trader

User = get_user_model()


class Strategy(models.Model):
    name = models.CharField(max_length=100)
    avg_profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    saved_avg_profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    custom_avg_profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    current_custom_profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    about = models.TextField()
    trader_deposit = models.DecimalField(default=0, decimal_places=2, max_digits=30, validators=[MinValueValidator(0)])
    total_deposited = models.DecimalField(default=0, decimal_places=2, max_digits=30, validators=[MinValueValidator(0)])
    min_deposit = models.DecimalField(default=0, decimal_places=2, max_digits=30)
    max_deposit = models.DecimalField(default=0, decimal_places=2, max_digits=30)
    total_copiers = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='strategies', null=True, blank=True)

    def __str__(self):
        return self.name


class StrategyProfitHistory(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='profits')
    value = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    date = models.DateTimeField(auto_now_add=True)


class UsersInStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='users')
    value = models.DecimalField(default=0, decimal_places=2, max_digits=30)
    date_of_adding = models.DateTimeField(auto_now_add=True)
    profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    saved_profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    custom_profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    different_profit_from_strategy = models.DecimalField(default=0, decimal_places=7, max_digits=30)
    current_custom_profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)

    class Meta:
        unique_together = ('user', 'strategy',)


class UserOutStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='out_strategies')
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='out_users')
    value = models.DecimalField(default=0, decimal_places=2, max_digits=30)
    date_of_adding = models.DateTimeField(default=timezone.now)
    date_of_out = models.DateTimeField(auto_now_add=True)
    profit = models.DecimalField(default=0, decimal_places=7, max_digits=30)
