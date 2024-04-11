import decimal
import random

import requests as rq

from transaction.models import Transaction


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


def create_transaction_on_change(crypto, trader, history):
    binance_url = "https://api.binance.com/api/v3/ticker/price"

    crypto_pair = crypto['name'] + "USDT"
    response = rq.get(f"{binance_url}?symbol={crypto_pair}")
    data = response.json()

    close_price = round(decimal.Decimal(data['price']), 7)
    roi = decimal.Decimal(random.randint(-1000, 5000) / 100)

    crypto_history = history[crypto_pair]
    side = crypto['side']

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

    Transaction.objects.create(
        trader=trader,
        crypto_pair=crypto_pair,
        side=side,
        open_price=open_price,
        close_price=close_price,
        roi=roi
    )
