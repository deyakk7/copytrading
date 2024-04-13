import decimal
import time

from celery import shared_task
from django.db import transaction as trans
from django.db.models import Avg

from strategy.models import Strategy, StrategyProfitHistory
from strategy.utils import get_percentage_change, get_current_exchange_rate_pair
from trader.models import Trader, TraderProfitHistory
from transaction.models import TransactionOpen


@shared_task
def calculate_avg_profit():
    strategies = Strategy.objects.exclude(trader=None)

    for strategy in strategies:
        opened_transactions = TransactionOpen.objects.filter(strategy=strategy)

        r = dict()
        w = dict()

        avg_profit = 0

        exchange_rate = get_current_exchange_rate_pair()

        for transaction in opened_transactions:
            r[transaction.crypto_pair] = get_percentage_change(
                transaction.crypto_pair,
                transaction.open_price,
                exchange_rate,
            )

            w[transaction.crypto_pair] = transaction.open_price

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

            trader_profit = trader.objects.aggregate(Avg('strategies__avg_profit'))['strategies__avg_profit']

            if trader_profit is None:
                trader_profit = 0

            trader.avg_profit_strategies = trader_profit

            trader.save()

    return 'done avg profit for strategies, traders, users_in_strategy'
    # r = get_last_percentage_change()
    # strategies = Strategy.objects.exclude(trader=None)
    #
    # for strategy in strategies:
    #     avg_profit = 0
    #     w = dict()
    #
    #     all_cryptos = strategy.crypto.all()
    #     for crypto in all_cryptos:
    #         w[crypto.name] = crypto.total_value
    #
    #     for crypto in all_cryptos:
    #         if crypto.side == 'long':
    #             avg_profit += (w[crypto.name.upper()] / decimal.Decimal(100)) * r[crypto.name.upper()]
    #         else:
    #             avg_profit -= (w[crypto.name.upper()] / decimal.Decimal(100)) * r[crypto.name.upper()]
    #
    #     with trans.atomic():
    #         strategy.refresh_from_db()
    #         strategy.avg_profit += avg_profit
    #         for user in strategy.users.all():
    #             user.profit += avg_profit
    #             user.save()
    #         strategy.save()
    #
    # for trader in Trader.objects.all():
    #     with trans.atomic():
    #         trader.refresh_from_db()
    #
    #         avg_profit = trader.strategies.aggregate(avg_profit=models.Avg('avg_profit'))['avg_profit']
    #
    #         trader.avg_profit_strategies = avg_profit
    #         trader.save()
    #
    # return 'done avg profit for strategies, traders, users_in_strategy'


@shared_task
@trans.atomic()
def saving_avg_profit():
    for strategy in Strategy.objects.exclude(trader=None):
        # strategy_last_data = StrategyProfitHistory.objects.filter(strategy=strategy).last()
        #
        # if strategy_last_data.value == strategy.avg_profit:
        #     continue

        StrategyProfitHistory.objects.create(strategy=strategy, value=strategy.avg_profit)

    for trader in Trader.objects.all():
        # trader_last_data = TraderProfitHistory.objects.filter(trader=trader).last()
        #
        # if trader_last_data.value == trader.roi:
        #     continue

        TraderProfitHistory.objects.create(trader=trader, value=trader.roi)

    return "saving avg_profit and traders' profit"


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
