import decimal
import time

from celery import shared_task
from django.db import transaction as trans, models

from strategy.models import Strategy, StrategyProfitHistory, UsersInStrategy
from strategy.utils import get_current_exchange_rate_usdt, \
    get_percentage_change, get_last_percentage_change_by_5_minutes
from trader.models import Trader


@shared_task
def calculate_avg_profit():
    r = get_last_percentage_change_by_5_minutes()
    strategies = Strategy.objects.all()

    for strategy in strategies:
        avg_profit = 0
        w = dict()

        all_cryptos = strategy.crypto.all()
        for crypto in all_cryptos:
            w[crypto.name] = crypto.total_value

        for crypto in all_cryptos:
            if crypto.side == 'long':
                avg_profit += (w[crypto.name.upper()] / decimal.Decimal(100)) * r[crypto.name.upper()]
            else:
                avg_profit -= (w[crypto.name.upper()] / decimal.Decimal(100)) * r[crypto.name.upper()]

        with trans.atomic():
            strategy.refresh_from_db()
            strategy.avg_profit += avg_profit + strategy.custom_avg_profit
            for user in strategy.users.all():
                user.profit += avg_profit + user.custom_avg_profit
                user.save()
            strategy.save()

    for trader in Trader.objects.all():
        avg_profit = trader.strategies.aggregate(avg_profit=models.Avg('avg_profit'))['avg_profit']
        trader.avg_profit_strategies = avg_profit
        trader.save()

    return 'done avg profit for strategies, traders, users_in_strategy'


@shared_task
def saving_avg_profit():
    for strategy in Strategy.objects.all():
        StrategyProfitHistory.objects.create(strategy=strategy, value=strategy.avg_profit)
    return "saving avg_profit"


@shared_task
def change_custom_profit(pk: int, data: dict):
    strategy = Strategy.objects.get(pk=pk)
    n = int(data['minutes'])
    percent = (decimal.Decimal(data['new_percentage_change_profit']) - strategy.custom_avg_profit) / n
    current_percent = percent
    while n > 0:
        with trans.atomic():
            strategy.refresh_from_db()
            strategy.current_custom_profit = current_percent
            strategy.save()
        time.sleep(1 * 60)
        current_percent += percent
        n -= 1
    with trans.atomic():
        strategy.refresh_from_db()
        strategy.current_custom_profit = 0
        strategy.custom_avg_profit = data['new_percentage_change_profit']
        strategy.save()

    return 'done custom avg profit'
