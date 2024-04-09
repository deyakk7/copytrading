import decimal
import math

from celery import shared_task
from django.db.models import Sum
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from trader.utils import random_time_full_change, random_time_small_change
from .models import Trader


@shared_task
def calculate_stats():
    for trader in Trader.objects.all():
        transactions = trader.transaction_set.all()
        if transactions.count() == 0:
            continue
        roi = round(transactions.aggregate(Sum('roi'))['roi__sum'] / transactions.count(), 2)

        profit_to_loss_ratio = round(
            transactions.filter(roi__gt=0).count() / transactions.filter(roi__lt=0).count(), 2)
        win_rate = round(transactions.filter(roi__gt=0).count() / transactions.count(), 4) * 100
        first_trade_time = transactions.order_by('close_time').first().close_time
        current_time = timezone.now()
        weekly_trades = round(transactions.count() / math.ceil((current_time - first_trade_time).days / 7), 2)
        if trader.avg_holding_time == "No info":
            avg_holding_time = random_time_full_change()
        else:
            avg_holding_time = random_time_small_change(trader.avg_holding_time)

        roi_deviation = math.sqrt(
            sum([(x.roi - roi) ** 2 for x in transactions]) / transactions.count()
        )
        sharpe_ratio = round(roi / decimal.Decimal(roi_deviation), 2)

        transactions_minus = transactions.filter(roi__lt=0)
        roi_minus = round(transactions_minus.aggregate(Sum('roi'))['roi__sum'] / transactions_minus.count(), 2)
        roi_deviation_minus = math.sqrt(
            sum([min(0, x.roi - roi_minus) ** 2 for x in transactions_minus]) / transactions_minus.count()
        )

        sortino_ratio = round(roi / decimal.Decimal(roi_deviation_minus), 2)
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
    schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)

    task = PeriodicTask.objects.update_or_create(
        name='calculate_stats',
        task='trader.tasks.calculate_stats',
        defaults={
            'interval': schedule,
        }
    )
    return task


run_calculate_stats()
