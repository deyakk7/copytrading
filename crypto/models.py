import requests as rq
from django.db import models

from strategy.models import Strategy


class Crypto(models.Model):
    name = models.CharField(max_length=30)
    total_value = models.DecimalField(max_digits=30, decimal_places=7)
    deposited_value = models.DecimalField(max_digits=30, decimal_places=7, default=0)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='crypto')


def get_tokens_pair():
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    response = rq.get(binance_url)
    data = response.json()
    return [token['symbol'] for token in data][:100]


TOKENS_PAIR = get_tokens_pair()
