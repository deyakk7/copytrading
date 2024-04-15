import decimal
import math

from celery import shared_task
from django.db.models import Sum, Avg
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from trader.utils import random_time_full_change, random_time_small_change, get_avg_holding_time
from transaction.models import TransactionClose
from .models import Trader


@shared_task
def calculate_stats():
    for trader in Trader.objects.all():
        transactions = TransactionClose.objects.filter(strategy__trader=trader)

        if transactions.count() == 0:
            continue

        roi = round(transactions.aggregate(roi_avg=Avg('roi'))['roi_avg'], 2)

        try:
            profit_to_loss_ratio = round(
                transactions.filter(roi__gt=0).count() / transactions.filter(roi__lt=0).count(), 2)
        except ZeroDivisionError:
            profit_to_loss_ratio = round(transactions.filter(roi__gt=0).count(), 2)

        try:
            win_rate = round(transactions.filter(roi__gt=0).count() / transactions.count(), 4) * 100
        except ZeroDivisionError:

            if transactions.filter(roi__gt=0).count():
                win_rate = 100.00
            else:
                win_rate = 0

        first_trade_time = transactions.order_by('close_time').first().close_time
        current_time = timezone.now()

        weekly_trades = round(transactions.count() / math.ceil(max((current_time - first_trade_time).days, 1) / 7), 2)

        avg_holding_time = get_avg_holding_time(transactions)

        roi_deviation = math.sqrt(
            sum([(x.roi - roi) ** 2 for x in transactions]) / transactions.count()
        )

        try:
            sharpe_ratio = round(roi / decimal.Decimal(roi_deviation), 2)
        except ZeroDivisionError:
            sharpe_ratio = 0.00

        transactions_minus = transactions.filter(roi__lt=0)

        if transactions_minus.count() > 0:
            roi_minus = round(
                transactions_minus.aggregate(roi_sum=Sum('roi'))['roi_sum'] / transactions_minus.count(), 2
            )
            roi_deviation_minus = math.sqrt(
                sum([min(0, x.roi - roi_minus) ** 2 for x in transactions_minus]) / transactions_minus.count()
            )

            try:
                sortino_ratio = round(roi / decimal.Decimal(roi_deviation_minus), 2)
            except ZeroDivisionError:
                sortino_ratio = 0.00

        else:
            sortino_ratio = 0.00

        roi_volatility = round(roi_deviation, 2)

        trader.roi = roi
        trader.profit_to_loss_ratio = profit_to_loss_ratio
        trader.win_rate = win_rate
        trader.weekly_trades = weekly_trades
        trader.avg_holding_time = avg_holding_time
        trader.roi_volatility = roi_volatility
        trader.sharpe_ratio = sharpe_ratio
        trader.sortino_ratio = sortino_ratio
        trader.last_traded_at = transactions.last().close_time

        trader.save()

    return 'Stats calculated'


def run_calculate_stats():
    schedule, _ = IntervalSchedule.objects.get_or_create(every=30, period=IntervalSchedule.SECONDS)

    PeriodicTask.objects.update_or_create(
        name='calculate_stats',
        task='trader.tasks.calculate_stats',
        defaults={
            'interval': schedule,
        }
    )


run_calculate_stats()
