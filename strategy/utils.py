import decimal

import requests as rq
from django.db import transaction as trans
from rest_framework import serializers

from crypto.models import Crypto
from strategy.models import Strategy
from transaction.models import TransactionOpen


def get_token_name():
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    response = rq.get(binance_url)
    data = response.json()
    return [token['symbol'][:-4] for token in data if token['symbol'].endswith('USDT')]


def get_current_exchange_rate_pair():
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    response = rq.get(binance_url)
    data = response.json()
    return {token['symbol']: decimal.Decimal(token['price']) for token in data}


def get_klines(symbol_input: str):
    if symbol_input == 'USDT':
        return decimal.Decimal(0)

    symbol = symbol_input + "USDT"
    url = "https://api.binance.com/api/v3/klines"

    params = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 6
    }

    response = rq.get(url, params=params)
    data = response.json()
    close_price_previous_hour = (float(data[0][4]) + float(data[0][1])) / 2
    close_current_price = float(data[5][4] + float(data[5][1])) / 2

    percentage_change = ((decimal.Decimal(close_current_price) - decimal.Decimal(
        close_price_previous_hour)) / decimal.Decimal(close_price_previous_hour)) * decimal.Decimal(100)
    return percentage_change


def get_percentage_change(symbol_input: str, old_rate: decimal.Decimal, exchange_rate: dict):
    if symbol_input == 'USDT':
        return decimal.Decimal(0)
    current_price = exchange_rate[symbol_input]
    try:
        percentage_change = ((decimal.Decimal(current_price) - decimal.Decimal(
            old_rate)) / decimal.Decimal(old_rate)) * decimal.Decimal(100)
    except ZeroDivisionError:
        percentage_change = decimal.Decimal(0)
    return percentage_change


CRYPTO_NAMES = get_token_name() + ['USDT']
CRYPTO_NAMES_TUPLE = [(name, name) for name in CRYPTO_NAMES]


def convert_to_usdt(data: dict, symbol: str, value: int):
    if symbol in CRYPTO_NAMES:
        symbol += "USDT"
        return decimal.Decimal(data[symbol]) * value
    elif symbol != 'USDT':
        symbol = "USDT" + symbol
        return decimal.Decimal(data[symbol]) / value
    else:
        return value


def get_current_exchange_rate_usdt():
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    response = rq.get(binance_url)
    data = response.json()
    result = {token['symbol'][:-4]: decimal.Decimal(token['price']) for token in data if
              token['symbol'].endswith('USDT')}
    result['USDT'] = decimal.Decimal(1)
    return result


def get_last_percentage_change():
    unique_crypto_names = Crypto.objects.values_list('name', flat=True).distinct()

    result = {}
    for name in unique_crypto_names:
        result[name] = get_klines(name)

    return result


def update_all_cryptos(strategy: Strategy, crypto_data: dict):
    usdt_value = 100 - sum([x['total_value'] for x in crypto_data if x['name'] != 'USDT'])

    crypto_names_new = [x['name'] for x in crypto_data if x['name'] != 'USDT']

    if usdt_value < 0:
        raise serializers.ValidationError({'error': 'Sum of percent must be less or equal than 100'})

    if usdt_value > 0:
        crypto_names_new.append("USDT")

        Crypto.objects.update_or_create(
            name='USDT',
            strategy=strategy,
            defaults={
                'side': None,
                'total_value': usdt_value
            }
        )

    crypto_to_delete = Crypto.objects.filter(
        strategy=strategy,
    ).exclude(
        name__in=crypto_names_new
    )

    crypto_to_delete.delete()

    for crypto in crypto_data:
        Crypto.objects.update_or_create(
            name=crypto['name'],
            strategy=strategy,
            defaults={
                'side': crypto['side'],
                'total_value': crypto['total_value']
            }
        )


@trans.atomic()
def recalculate_percentage_in_strategy(strategy: Strategy, exchange_rate: dict):
    transactions = TransactionOpen.objects.filter(
        strategy=strategy,
    )

    available_pool = strategy.available_pool
    trader_deposit = available_pool

    dict_data = {}

    for transaction_op in transactions:

        money_in_transaction = transaction_op.value * exchange_rate[transaction_op.crypto_pair]

        trader_deposit += money_in_transaction
        dict_data[transaction_op.crypto_pair[:-4]] = money_in_transaction

    sum_of_trader_deposit = 0

    for transaction_op in transactions:
        token_name = transaction_op.crypto_pair[:-4]

        transaction_op.percentage = (dict_data[token_name] / trader_deposit) * 100
        transaction_op.save()

        crypto_db: Crypto = Crypto.objects.filter(strategy=strategy, name=token_name).first()

        crypto_db.total_value = transaction_op.percentage
        crypto_db.save()

    crypto_usdt: Crypto = Crypto.objects.filter(
        strategy=strategy,
        name='USDT'
    ).first()

    if available_pool == 0:
        if crypto_usdt is not None:
            crypto_usdt.delete()
            return

    strategy.trader_deposit = trader_deposit
    strategy.save()

    if crypto_usdt is None:
        Crypto.objects.create(
            strategy=strategy,
            name='USDT',
            total_value=(available_pool / trader_deposit) * 100,
            side=None
        )
        return

    crypto_usdt.total_value = (available_pool / trader_deposit) * 100
    crypto_usdt.save()
