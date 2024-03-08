from django.db import models

from strategy.models import Strategy


class Crypto(models.Model):
    name = models.CharField(max_length=30)
    value = models.DecimalField(max_digits=30, decimal_places=7)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='crypto')
