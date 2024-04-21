import decimal
import random
from math import gcd

import requests as rq

from crypto.models import Crypto
from strategy.models import Strategy
from strategy.utils import get_percentage_change
from transaction.models import TransactionClose, TransactionOpen


def saving_crypto_data_24h():
    binance_url = "https://api.binance.com/api/v3/ticker/24hr"
    response = rq.get(binance_url)
    data = response.json()
    result = {}
    for token in data:
        if token['symbol'][-4:] != 'USDT' or token['highPrice'] == '0.00000000':
            continue

        result[
            token['symbol']
        ] = {
            "highest_price": decimal.Decimal(token['highPrice']),
            "lowest_price": decimal.Decimal(token['lowPrice']),
        }

    return result


def create_transaction_on_change(crypto, trader, history, new_side):
    binance_url = "https://api.binance.com/api/v3/ticker/price"

    crypto_pair = crypto['name'] + "USDT"
    response = rq.get(f"{binance_url}?symbol={crypto_pair}")
    data = response.json()

    close_price = round(decimal.Decimal(data['price']), 7)
    roi = decimal.Decimal(random.randint(-1000, 5000) / 100)

    crypto_history = history[crypto_pair]
    side = new_side

    while roi == 0:
        roi = decimal.Decimal(random.randint(-1000, 5000) / 100)
    if roi > 0 and side == "long" or roi < 0 and side == 'short':
        open_price = decimal.Decimal(
            random.randint(int(crypto_history['lowest_price'] * 10 ** 7),
                           int(close_price * 10 ** 7 - 1)) / 10 ** 7)
    else:
        open_price = decimal.Decimal(
            random.randint(int(close_price * 10 ** 7 + 1),
                           int(crypto_history['highest_price'] * 10 ** 7)) / 10 ** 7)

    TransactionClose.objects.create(
        trader=trader,
        crypto_pair=crypto_pair,
        side=side,
        open_price=open_price,
        close_price=close_price,
        roi=roi
    )


def create_open_transaction(crypto_data: dict, exchange_rate: dict[str, decimal.Decimal]):
    if crypto_data['name'] == 'USDT':
        return

    strategy = crypto_data['strategy']
    crypto_pair = crypto_data['name'] + "USDT"
    side = crypto_data['side']
    open_price = exchange_rate[crypto_data['name']]
    total_value = crypto_data['total_value']

    TransactionOpen.objects.create(
        strategy_id=strategy,
        crypto_pair=crypto_pair,
        side=side,
        open_price=open_price,
        total_value=total_value,
    )


def create_close_transaction(crypto_data: TransactionOpen, exchange_rate: dict[str, decimal.Decimal]):
    if crypto_data.crypto_pair == 'USDT':
        return

    strategy = crypto_data.strategy
    crypto_pair = crypto_data.crypto_pair
    side = crypto_data.side
    open_price = crypto_data.open_price
    open_time = crypto_data.open_time
    close_price = exchange_rate[crypto_pair[:-4]]
    total_value = crypto_data.total_value

    if open_price > close_price and side == "short" or open_price < close_price and side == "long":
        roi = random.randint(100, 7000) / 100
    else:
        roi = random.randint(-4000, -100) / 100

    percentage_change = get_percentage_change(crypto_pair[:-4], open_price, exchange_rate)

    saved_profit = (total_value / 100) * percentage_change

    TransactionClose.objects.create(
        strategy=strategy,
        crypto_pair=crypto_pair,
        side=side,
        open_price=open_price,
        close_price=close_price,
        total_value=total_value,
        roi=roi,
        open_time=open_time
    )

    strategy.saved_avg_profit += saved_profit
    strategy.save()


def averaging_open_transaction(crypto_bf: dict, crypto_db: Crypto, transaction_op: TransactionOpen, exchange_rate):
    total_value_bf = crypto_bf['total_value']
    total_value_new = crypto_db.total_value - crypto_bf['total_value']

    open_price_bf = transaction_op.open_price
    open_price_new = exchange_rate[crypto_db.name]

    new_open_price = ((total_value_bf * open_price_bf + total_value_new * open_price_new) /
                      (total_value_new + total_value_bf))

    transaction_op.total_value = crypto_db.total_value
    transaction_op.open_price = new_open_price

    transaction_op.save()
