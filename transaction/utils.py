import requests as rq

from crypto.models import CryptoPriceHistory24h


def saving_crypto_data_24h():
    binance_url = "https://api.binance.com/api/v3/ticker/24hr"
    response = rq.get(binance_url)
    data = response.json()
    for token in data:
        if token['symbol'][-4:] != 'USDT' or token['highPrice'] == '0.00000000':
            continue
        name = token['symbol']
        highest_price = token['highPrice']
        lowest_price = token['lowPrice']
        CryptoPriceHistory24h.objects.update_or_create(
            name=name,
            defaults={
                'highest_price': highest_price,
                'lowest_price': lowest_price,
            }
        )
