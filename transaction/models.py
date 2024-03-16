from django.db import models

from trader.models import Trader


class Transaction(models.Model):
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    crypto_pair = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=30, decimal_places=7)
    amount = models.DecimalField(max_digits=30, decimal_places=7)
    side = models.BooleanField()
