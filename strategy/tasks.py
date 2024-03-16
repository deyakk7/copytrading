import decimal

import requests as rq
from celery import shared_task

from crypto.models import Crypto
from strategy.models import Strategy


def get_token_name():
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    response = rq.get(binance_url)
    data = response.json()
    return [token['symbol'][:-4] for token in data if token['symbol'].endswith('USDT')]


def get_current_exchange_rate():
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    response = rq.get(binance_url)
    data = response.json()
    return {token['symbol']: token['price'] for token in data}


def get_klines(symbol_input: str):
    if symbol_input == 'USDT':
        return decimal.Decimal(0)

    symbol = symbol_input + "USDT"
    url = "https://api.binance.com/api/v3/klines"

    params = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 61
    }

    response = rq.get(url, params=params)
    data = response.json()
    close_price_previous_hour = float(data[0][4])
    close_current_price = float(data[60][4])

    percentage_change = ((decimal.Decimal(close_current_price) - decimal.Decimal(
        close_price_previous_hour)) / decimal.Decimal(close_price_previous_hour)) * decimal.Decimal(100)
    return percentage_change


CRYPTO_NAMES = get_token_name()


def convert_to_usdt(data: dict, symbol: str, value: int):
    if symbol in CRYPTO_NAMES:
        symbol += "USDT"
        return decimal.Decimal(data[symbol]) * value
    elif symbol != 'USDT':
        symbol = "USDT" + symbol
        return decimal.Decimal(data[symbol]) / value
    else:
        return value


@shared_task
def check_task():
    exchange_rate = get_current_exchange_rate()
    strategies = Strategy.objects.all()
    cryptos = [i['name'] for i in Crypto.objects.values('name').distinct()]
    r = dict()
    for crypto in cryptos:
        r[crypto.upper()] = get_klines(crypto.upper())
    for strategy in strategies:
        avg_profit = 0

        all_cryptos_in_strategy = dict()
        all_usdt_in_profile = decimal.Decimal(0)
        all_cryptos = strategy.crypto.all()
        for crypto in all_cryptos:
            crypto_in_usdt = convert_to_usdt(exchange_rate, crypto.name.upper(), crypto.total_value)
            all_cryptos_in_strategy[crypto.name.upper()] = crypto_in_usdt
            all_usdt_in_profile += crypto_in_usdt

        w = {name.upper(): decimal.Decimal(value) / decimal.Decimal(all_usdt_in_profile) * decimal.Decimal(100) for
             name, value in
             all_cryptos_in_strategy.items()}

        for crypto in all_cryptos:
            avg_profit += (w[crypto.name.upper()] / decimal.Decimal(100)) * r[crypto.name.upper()]
        strategy.avg_profit = avg_profit
        strategy.save()
