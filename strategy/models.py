from django.db import models

from trader.models import Trader


class Strategy(models.Model):
    name = models.CharField(max_length=100)
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='strategies')
