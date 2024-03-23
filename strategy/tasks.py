import decimal
import math
import time
from django.db import transaction as trans
from celery import shared_task

from strategy.models import Strategy
from strategy.utils import get_current_exchange_rate_pair, convert_to_usdt, get_current_exchange_rate_usdt, \
    get_percentage_change
from trader.models import Trader


@shared_task
def calculate_avg_profit():
    exchange_rate_pair = get_current_exchange_rate_pair()
    exchange_rate = get_current_exchange_rate_usdt()
    strategies = Strategy.objects.all()

    for strategy in strategies:
        avg_profit = 0
        r = dict()

        all_cryptos_in_strategy = dict()
        all_usdt_in_profile = decimal.Decimal(0)
        all_cryptos = strategy.crypto.all()
        for crypto in all_cryptos:
            r[crypto.name.upper()] = get_percentage_change(crypto.name, crypto.exchange_rate, exchange_rate)
            crypto_in_usdt = convert_to_usdt(exchange_rate_pair, crypto.name.upper(), crypto.total_value)
            all_cryptos_in_strategy[crypto.name.upper()] = crypto_in_usdt
            all_usdt_in_profile += crypto_in_usdt

        w = {name.upper(): decimal.Decimal(value) / decimal.Decimal(all_usdt_in_profile) * decimal.Decimal(100) for
             name, value in
             all_cryptos_in_strategy.items()}

        for crypto in all_cryptos:
            avg_profit += (w[crypto.name.upper()] / decimal.Decimal(100)) * r[crypto.name.upper()]
        with trans.atomic():
            strategy.refresh_from_db()
            strategy.avg_profit = avg_profit + strategy.custom_avg_profit + strategy.current_custom_profit
            strategy.save()

    for trader in Trader.objects.all():
        all_strategies = trader.strategies.all()
        avg_profit = 0
        for strategy in all_strategies:
            avg_profit += strategy.avg_profit
        trader.avg_profit_strategies = avg_profit / len(all_strategies)
        trader.save()

    return 'done avg profit'


@shared_task
def change_custom_profit(pk: int, data: dict):
    strategy = Strategy.objects.get(pk=pk)
    n = math.ceil(data['minutes'] / 5)
    percent = (decimal.Decimal(data['new_percentage_change_profit']) - strategy.custom_avg_profit) / n
    current_percent = percent
    while n > 0:
        time.sleep(5 * 60)
        with trans.atomic():
            strategy.refresh_from_db()
            strategy.current_custom_profit = current_percent
            strategy.save()
        current_percent += percent
        n -= 1
    with trans.atomic():
        strategy.refresh_from_db()
        strategy.current_custom_profit = 0
        strategy.custom_avg_profit = data['new_percentage_change_profit']
        strategy.save()

    return 'done custom avg profit'
