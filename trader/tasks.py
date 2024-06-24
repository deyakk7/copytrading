import decimal
import math

from celery import shared_task
from django.db.models import Sum, Avg
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from strategy.utils import get_current_exchange_rate_usdt
from trader.utils import get_avg_holding_time
from transaction.models import TransactionClose, TransactionOpen
from transaction.utils import calculate_roi
from .models import Trader, TrendingThreshold


@shared_task
def calculate_stats():
    trending_threshold = TrendingThreshold.objects.first()
    if trending_threshold is None:
        trending_threshold = TrendingThreshold.objects.create(
            min_copiers=10
        )
    exchange_rate_usdt = get_current_exchange_rate_usdt()

    for trader in Trader.objects.all():
        transactions_closed = TransactionClose.objects.filter(strategy__trader=trader)
        transactions_opened = TransactionOpen.objects.filter(strategy__trader=trader)

        if trader.copiers_count >= trending_threshold.min_copiers:
            trader.trader_type = 'trending'
        else:
            trader.trader_type = None

        trader.save()

        roi_opened = 0
        roi_closed = 0

        for transaction in transactions_opened:
            roi_opened += calculate_roi(transaction, exchange_rate_usdt)

        for transaction in transactions_closed:
            roi_closed += calculate_roi(transaction, exchange_rate_usdt)

        if transactions_closed.count() + transactions_opened.count() != 0:
            roi = (roi_opened + roi_closed) / (transactions_closed.count() + transactions_opened.count())
            trader.roi = roi

            last_open_trans = transactions_opened.last().open_time
            last_closed_trans = transactions_closed.last()
            if last_closed_trans is None:
                last_closed_trans = last_open_trans
            else:
                last_closed_trans = last_closed_trans.close_time

            trader.last_traded_at = last_open_trans if last_open_trans > last_closed_trans else last_closed_trans

            trader.save()

        else:
            continue

        if transactions_closed.count() == 0:
            continue

        try:
            profit_to_loss_ratio = round(
                transactions_closed.filter(roi__gt=0).count() / transactions_closed.filter(roi__lt=0).count(), 2)
        except ZeroDivisionError:
            profit_to_loss_ratio = round(transactions_closed.filter(roi__gt=0).count(), 2)

        try:
            win_rate = round(transactions_closed.filter(roi__gt=0).count() / transactions_closed.count(), 4) * 100
        except ZeroDivisionError:

            if transactions_closed.filter(roi__gt=0).count():
                win_rate = 100.00
            else:
                win_rate = 0

        first_trade_time = transactions_closed.order_by('close_time').first().close_time
        current_time = timezone.now()

        weekly_trades = round(transactions_closed.count() / math.ceil(max((current_time - first_trade_time).days, 1) / 7), 2)

        avg_holding_time = get_avg_holding_time(transactions_closed)

        roi_deviation = math.sqrt(
            sum([(x.roi - roi_closed) ** 2 for x in transactions_closed]) / transactions_closed.count()
        )

        try:
            sharpe_ratio = round(roi_closed / decimal.Decimal(roi_deviation), 2)
        except ZeroDivisionError:
            sharpe_ratio = 0.00

        transactions_minus = transactions_closed.filter(roi__lt=0)

        if transactions_minus.count() > 0:
            roi_minus = transactions_minus.aggregate(roi_sum=Sum('roi'))['roi_sum'] / transactions_minus.count()

            roi_deviation_minus = math.sqrt(
                sum([(x.roi - roi_minus) ** 2 for x in transactions_minus]) / transactions_minus.count()
            )

            try:
                sortino_ratio = round(roi_closed / decimal.Decimal(roi_deviation_minus), 2)
            except ZeroDivisionError:
                sortino_ratio = 0.00

        else:
            sortino_ratio = 0.00

        roi_volatility = round(roi_deviation, 2)

        trader.profit_to_loss_ratio = profit_to_loss_ratio
        trader.win_rate = win_rate
        trader.weekly_trades = weekly_trades
        trader.avg_holding_time = avg_holding_time
        trader.roi_volatility = roi_volatility
        trader.sharpe_ratio = sharpe_ratio
        trader.sortino_ratio = sortino_ratio

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
