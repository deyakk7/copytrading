import decimal

import requests as rq


def get_token_name():
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    response = rq.get(binance_url)
    data = response.json()
    return [token['symbol'][:-4] for token in data if token['symbol'].endswith('USDT')]


def get_current_exchange_rate_pair():
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
    result = {token['symbol'][:-4]: token['price'] for token in data if token['symbol'].endswith('USDT')}
    result['USDT'] = 1
    return result
