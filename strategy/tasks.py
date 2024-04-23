import decimal
import time

from celery import shared_task
from django.db import transaction as trans
from django.db.models import Avg
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from strategy.models import Strategy, StrategyProfitHistory
from strategy.utils import get_percentage_change, get_current_exchange_rate_pair, recalculate_percentage_in_strategy
from trader.models import Trader, TraderProfitHistory
from transaction.models import TransactionOpen


@shared_task
@trans.atomic()
def calculate_avg_profit():
    strategies = Strategy.objects.exclude(trader=None)
    exchange_rate = get_current_exchange_rate_pair()

    for strategy in strategies:
        recalculate_percentage_in_strategy(strategy, exchange_rate)
        opened_transactions = TransactionOpen.objects.filter(strategy=strategy)

        r = dict()
        w = dict()

        avg_profit = 0

        for transaction in opened_transactions:
            r[transaction.crypto_pair] = get_percentage_change(
                transaction.crypto_pair,
                transaction.open_price,
                exchange_rate,
            )

            w[transaction.crypto_pair] = transaction.percentage

            if transaction.side == 'long':
                avg_profit += (w[transaction.crypto_pair] / decimal.Decimal(100)) * r[transaction.crypto_pair]
            else:
                avg_profit -= (w[transaction.crypto_pair] / decimal.Decimal(100)) * r[transaction.crypto_pair]

        strategy.avg_profit = strategy.saved_avg_profit + avg_profit + strategy.custom_avg_profit

        with trans.atomic():
            for user in strategy.users.all():
                user.profit = (
                        strategy.avg_profit -
                        user.custom_profit -
                        user.different_profit_from_strategy +
                        user.saved_profit
                )

                user.save()

            strategy.save()

    with trans.atomic():
        for trader in Trader.objects.all():
            trader.refresh_from_db()

            aggregation_result = trader.strategies.aggregate(avg_profit=Avg('avg_profit'))

            trader_profit = aggregation_result['avg_profit'] or 0

            trader.avg_profit_strategies = trader_profit
            trader.save()

    return 'done avg profit for strategies, traders, users_in_strategy'


@shared_task
@trans.atomic()
def saving_avg_profit():
    for strategy in Strategy.objects.exclude(trader=None):
        strategy_last_data = StrategyProfitHistory.objects.filter(strategy=strategy).last()

        if strategy_last_data is None:
            StrategyProfitHistory.objects.create(strategy=strategy, value=0)
            continue

        if strategy_last_data.value == strategy.avg_profit:
            continue

        StrategyProfitHistory.objects.create(strategy=strategy, value=strategy.avg_profit)

    for trader in Trader.objects.all():
        trader_last_data = TraderProfitHistory.objects.filter(trader=trader).last()

        if trader_last_data is None:
            TraderProfitHistory.objects.create(trader=trader, value=0)
            continue

        if trader_last_data.value == trader.roi:
            continue

        TraderProfitHistory.objects.create(trader=trader, value=trader.roi)

    return "saving avg_profit and traders' profit"


def strategy_task_runner():
    schedule_calculate_avg, _ = IntervalSchedule.objects.get_or_create(every=30, period=IntervalSchedule.SECONDS)
    schedule_saving_avg, _ = IntervalSchedule.objects.get_or_create(every=10, period=IntervalSchedule.MINUTES)

    PeriodicTask.objects.update_or_create(
        name='calculate_avg_profit',
        task='strategy.tasks.calculate_avg_profit',
        defaults={
            'interval': schedule_calculate_avg,
        }
    )

    PeriodicTask.objects.update_or_create(
        name='saving_avg_profit',
        task='strategy.tasks.saving_avg_profit',
        defaults={
            'interval': schedule_saving_avg,
        }
    )


strategy_task_runner()
