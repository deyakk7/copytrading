import datetime
import random

from django.db.models import QuerySet, ExpressionWrapper, F, Avg, fields

from transaction.models import TransactionClose


def random_time_full_change():
    minutes = random.randint(1, 2880)  # 2 days = 2880 minutes

    if minutes < 60:
        return f"{minutes} minutes"
    elif minutes < 1440:
        hours = minutes / 60
        return f"{round(hours, 2)} hours"
    else:
        days = minutes / 1440
        return f"{round(days, 2)} days"


def random_time_small_change(holding_time: str):
    time, str_time = holding_time.split(' ')

    if str_time == 'minutes':
        minutes = int(time)
        a = random.randint(minutes - 10, minutes)
        if a < 1:
            a = 1
        b = random.randint(minutes, minutes + 10)
        if b > 59:
            b = 59
        minutes = random.randint(a, b)
        return f"{minutes} {str_time}"

    if str_time == 'hours':
        hours = int(float(time) * 100)
        a = random.randint(hours - 100, hours)
        if a < 100:
            a = 100
        b = random.randint(hours, hours + 100)
        if b > 2399:
            b = 2399

        hours = random.randint(a, b) / 100
        return f"{hours} {str_time}"

    if str_time == 'days':
        days = int(float(time) * 100)
        a = random.randint(days - 50, days)
        if a < 100:
            a = 100
        b = random.randint(days, days + 50)
        if b > 300:
            b = 300
        days = random.randint(a, b) / 100
        return f"{days} {str_time}"

    return f"{time + '1'} {str_time}"


def get_avg_holding_time(transactions: QuerySet[TransactionClose]):
    avg_holding_seconds = transactions.annotate(
        holding_time=ExpressionWrapper(F('close_time') - F('open_time'), output_field=fields.DurationField())
    ).aggregate(avg_holding_time=Avg('holding_time'))

    avg_holding_time = avg_holding_seconds['avg_holding_time']

    if avg_holding_time is not None:

        total_seconds = avg_holding_time.total_seconds()

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 1:
            avg_holding_str = f"{int(days)}.{int(hours / 24 * 10)} days"
        elif hours > 1:
            avg_holding_str = f"{int(hours)}.{int(minutes / 60 * 10)} hours"
        elif minutes > 1:
            avg_holding_str = f"{int(minutes)}.{int(seconds / 60 * 10)} minutes"
        else:
            avg_holding_str = f"{int(seconds)} seconds"
    else:
        avg_holding_str = "No data"

    return avg_holding_str
