import requests as rq
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from strategy.models import Strategy, UsersInStrategy
from strategy.utils import CRYPTO_NAMES_TUPLE


class Crypto(models.Model):
    name = models.CharField(max_length=30)
    total_value = models.DecimalField(max_digits=5, decimal_places=2,
                                      validators=[MaxValueValidator(100), MinValueValidator(0)])
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='crypto')
    exchange_rate = models.DecimalField(max_digits=30, decimal_places=7, default=0)
    side = models.CharField(max_length=10, choices=(('short', 'short'), ('long', 'long')), default='long', null=True,
                            blank=True)

    def __str__(self):
        return f"(ST) {self.name} - {self.exchange_rate} -- {self.id}"


class CryptoInUser(models.Model):
    name = models.CharField(max_length=30, choices=CRYPTO_NAMES_TUPLE)
    total_value = models.DecimalField(max_digits=5, decimal_places=2,
                                      validators=[MaxValueValidator(100), MinValueValidator(0)])
    exchange_rate = models.DecimalField(max_digits=30, decimal_places=7, default=0)
    side = models.CharField(max_length=10, choices=(('short', 'short'), ('long', 'long')), default='long', null=True,
                            blank=True)

    user_in_strategy = models.ForeignKey(UsersInStrategy, on_delete=models.CASCADE, related_name='crypto')

    def __str__(self):
        return f"{self.name} - {self.exchange_rate} -- {self.id}"


class CryptoPriceHistory24h(models.Model):
    name = models.CharField(max_length=30)
    highest_price = models.DecimalField(max_digits=30, decimal_places=7, default=0)
    lowest_price = models.DecimalField(max_digits=30, decimal_places=7, default=0)

    def __str__(self):
        return f"{self.name} - {self.lowest_price} - {self.highest_price}"


def get_tokens_pair():
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    response = rq.get(binance_url)
    data = response.json()
    return [token['symbol'] for token in data][:100]


TOKENS_PAIR = get_tokens_pair()
