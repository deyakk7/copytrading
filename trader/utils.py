import random


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
