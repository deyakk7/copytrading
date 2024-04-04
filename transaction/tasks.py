import decimal
import random
import time

import requests as rq
from celery import shared_task
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from crypto.models import CryptoPriceHistory24h
from strategy.models import Strategy
from transaction.models import Transaction
from transaction.utils import saving_crypto_data_24h


@shared_task
def get_highest_lowest_price():
    saving_crypto_data_24h()


def run_get_highest_lowest_price():
    schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS)

    task = PeriodicTask.objects.update_or_create(
        name='get_highest_lowest_price',
        task='transaction.tasks.get_highest_lowest_price',
        defaults={
            'interval': schedule,
        }
    )
    return task


run_get_highest_lowest_price()


@shared_task
def create_transaction():
    binance_url = "https://api.binance.com/api/v3/ticker/price"

    all_strategies = Strategy.objects.filter(trader__isnull=False).order_by('?')
    used_traders_id = set()
    for strategy in all_strategies:
        time.sleep(random.randint(17, 57))
        if strategy.trader.id in used_traders_id:
            continue
        used_traders_id.add(strategy.trader.id)
        crypto = strategy.crypto.exclude(name='USDT').order_by('?').first()
        if crypto is None:
            continue
        crypto_pair = crypto.name + "USDT"
        response = rq.get(f"{binance_url}?symbol={crypto_pair}")
        data = response.json()
        close_price = round(decimal.Decimal(data['price']), 7)
        roi = decimal.Decimal(random.randint(-10000, 10000) / 100)
        crypto_history = CryptoPriceHistory24h.objects.filter(name=crypto_pair).first()
        if crypto_history is None:
            saving_crypto_data_24h()
            continue
        side = crypto.side
        while roi == 0:
            roi = decimal.Decimal(random.randint(-10000, 10000) / 100)
        if roi > 0 and side == "long" or roi < 0 and side == 'short':
            open_price = decimal.Decimal(
                random.randint(int(crypto_history.lowest_price * 10 ** 7), int(close_price * 10 ** 7)) / 10 ** 7 - 1)
        else:
            open_price = decimal.Decimal(
                random.randint(int(close_price * 10 ** 7 + 1), int(crypto_history.highest_price * 10 ** 7)) / 10 ** 7)

        Transaction.objects.create(
            trader=strategy.trader,
            crypto_pair=crypto_pair,
            side=side,
            open_price=open_price,
            close_price=close_price,
            roi=roi
        )

    return "Done autotrading"


def run_create_transaction():
    schedule, _ = IntervalSchedule.objects.get_or_create(every=10, period=IntervalSchedule.MINUTES)

    task = PeriodicTask.objects.update_or_create(
        name='create_transaction',
        task='transaction.tasks.create_transaction',
        defaults={
            'interval': schedule,
        }
    )
    return task


run_create_transaction()
