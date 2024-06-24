import random
import time
from collections import OrderedDict

import pandas as pd
import pandas_ta as ta
from binance.client import Client
from django.core.management.base import BaseCommand

from crypto.models import Crypto
from strategy.models import Strategy
from strategy.serializers import StrategySerializer
from strategy.utils import TOKEN_AVAILABLE_LIST

client = Client(api_key='HqSuAXR1mIIKrrj0pwcPRkIu5DANXde8mjhlX8VLwmkdT3aVaC1UghuOSlu7zbOy',
                        api_secret='LaQc74yx2JvJIkeDyjdYZFgNmI3DXtD6YHUcSE17Szbm6w12qfTx4M9EbtstDyH2')


class Command(BaseCommand):
    help = 'Run auto trading loop'

    def add_to_pull(self, symbol, action):
        symbol = symbol[:-4]
        strategies = Strategy.objects.filter(trader__auto_trading=True).order_by('?')
        for strategy in strategies:
            cryptos = strategy.crypto.all()

            if symbol in [crypto.name for crypto in cryptos]:
                usdt_crypto = cryptos.filter(name='USDT').first()
                current_crypto: Crypto = cryptos.filter(name=symbol).first()

                result_data = {'crypto': []}

                if (action == 'buy' and current_crypto.side == 'long' or action == 'sell' and current_crypto.side == 'short') and usdt_crypto is not None:
                    total_value = random.randint(1, 100)
                    result_data['new_cryptos'] = [{'name': symbol, 'total_value': total_value, 'side': current_crypto.side}]

                    for crypto_db in cryptos:
                        result_data['crypto'].append({
                            'name': crypto_db.name,
                            'total_value': 100,
                            'side': crypto_db.side
                        })

                    print('Increase:', symbol, 'on strategy', strategy.name, 'by', total_value)

                elif action == 'sell' and current_crypto.side == 'long' or action == 'buy' and current_crypto.side == 'short':
                    cryptos = cryptos.exclude(name=symbol)

                    for crypto_db in cryptos:
                        result_data['crypto'].append({
                            'name': crypto_db.name,
                            'total_value': 100,
                            'side': crypto_db.side
                        })

                    new_total_value = random.randint(1, 99)

                    result_data['crypto'].append({
                        'name': current_crypto.name,
                        'total_value': new_total_value,
                        'side': current_crypto.side
                    })

                    result_data['new_cryptos'] = []
                    print(f'Decrease: {symbol} on strategy {strategy.name} by {new_total_value}')
                else:
                    continue

                serializer = StrategySerializer(strategy, data=result_data, partial=True,
                                                context={'request': None})

                ordered_data_dict = OrderedDict(result_data)

                if serializer.is_valid():
                    serializer.update(strategy, ordered_data_dict)

                    print('Updated strategy with new cryptos')
                else:
                    print('Failed to update strategy:', serializer.errors)
                return

    def get_exchange_rate_autotrading(self):
        exchange_info = client.get_exchange_info()
        symbols = [symbol['symbol'] for symbol in exchange_info['symbols'] if
                   'USDT' in symbol['symbol'] and symbol['symbol'][:-4] in TOKEN_AVAILABLE_LIST]
        return symbols

    def ATR_indicator(self, *args, **kwargs):

        def get_atr(symbol, interval, limit=500):
            klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
            highs = [float(entry[2]) for entry in klines]
            lows = [float(entry[3]) for entry in klines]
            closes = [float(entry[4]) for entry in klines]

            df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
            atr = ta.atr(df['high'], df['low'], df['close'])

            df['ATR'] = atr

            return df['ATR'].iloc[-1], df['close'].iloc[-1]

        print("Checking ATR values...")

        symbols = self.get_exchange_rate_autotrading()

        for symbol in symbols:
            timeframes = ['30m']
            signals = {"buy": 0, "sell": 0}

            for tf in timeframes:
                atr, close = get_atr(symbol, tf)

                if close > 5 * atr:
                    signals["buy"] += 1
                elif close < 0.2 * atr:
                    signals["sell"] += 1

            if signals["buy"] > signals["sell"]:
                self.add_to_pull(symbol, 'buy')

            elif signals["sell"] > signals["buy"]:
                self.add_to_pull(symbol, 'sell')

        time_to_sleep = random.randint(30, 180)
        time.sleep(time_to_sleep)

    def bolinger_indicator(self):
        def get_bollinger_bands(symbol, interval, limit=500):
            klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
            closes = [float(entry[4]) for entry in klines]

            df = pd.DataFrame(closes, columns=["close"])
            bbands = ta.bbands(df['close'])

            df = df.join(bbands)
            return df[['BBL_5_2.0', 'BBM_5_2.0', 'BBU_5_2.0', 'close']].iloc[-1]

        print("Checking Bollinger Bands values...")

        symbols = self.get_exchange_rate_autotrading()

        for symbol in symbols:
            timeframes = ['30m', '1h', '2h', '4h', '1d']
            signals = {"long": 0, "short": 0}

            for tf in timeframes:
                bb_values = get_bollinger_bands(symbol, tf)
                lower_band = bb_values['BBL_5_2.0']
                upper_band = bb_values['BBU_5_2.0']
                close = bb_values['close']

                if close <= lower_band:
                    signals["long"] += 1
                elif close >= upper_band:
                    signals["short"] += 1

            if signals["long"] > signals["short"]:
                self.add_to_pull(symbol, 'buy')

            elif signals["short"] > signals["long"]:
                self.add_to_pull(symbol, 'sell')

        time_to_sleep = random.randint(30, 180)
        time.sleep(time_to_sleep)

    def fibonacci_indicator(self):
        def get_fibonacci_levels(symbol, interval, limit=500):
            klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
            high_prices = [float(entry[2]) for entry in klines]
            low_prices = [float(entry[3]) for entry in klines]
            close = float(klines[-1][4])

            max_price = max(high_prices)
            min_price = min(low_prices)

            diff = max_price - min_price
            level_1 = max_price - 0.236 * diff
            level_2 = max_price - 0.382 * diff
            level_3 = max_price - 0.618 * diff

            return {
                "close": close,
                "level_1": level_1,
                "level_2": level_2,
                "level_3": level_3,
                "max_price": max_price,
                "min_price": min_price
            }

        print("Checking Fibonacci retracement levels...")

        symbols = self.get_exchange_rate_autotrading()

        for symbol in symbols:
            timeframes = ['30m', '1h', '2h', '4h', '1d']
            signals = {"long": 0, "short": 0}

            for tf in timeframes:
                fib_levels = get_fibonacci_levels(symbol, tf)
                close = fib_levels['close']
                level_1 = fib_levels['level_1']
                level_2 = fib_levels['level_2']
                level_3 = fib_levels['level_3']

                if close >= level_1:
                    signals["long"] += 1
                elif close <= level_3:
                    signals["short"] += 1

            if signals["long"] > signals["short"]:
                self.add_to_pull(symbol, 'buy')

            elif signals["short"] > signals["long"]:
                self.add_to_pull(symbol, 'sell')

        time_to_sleep = random.randint(30, 180)
        time.sleep(time_to_sleep)


    def moving_average_indicator(self):

        def get_moving_averages(symbol, interval, limit=500):
            klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
            closes = [float(entry[4]) for entry in klines]

            df = pd.DataFrame(closes, columns=["close"])
            sma = ta.sma(df['close'], length=20)
            ema = ta.ema(df['close'], length=20)

            df['SMA_20'] = sma
            df['EMA_20'] = ema

            return df[['SMA_20', 'EMA_20', 'close']].iloc[-1]

        print("Checking Moving Averages values...")

        symbols = self.get_exchange_rate_autotrading()

        for symbol in symbols:
            timeframes = ['30m', '1h', '2h', '4h', '1d']
            signals = {"long": 0, "short": 0}

            for tf in timeframes:
                ma_values = get_moving_averages(symbol, tf)
                sma = ma_values['SMA_20']
                ema = ma_values['EMA_20']
                close = ma_values['close']

                if close > sma and close > ema:
                    signals["long"] += 1
                elif close < sma and close < ema:
                    signals["short"] += 1

            if signals["long"] > signals["short"]:
                self.add_to_pull(symbol, 'buy')
            elif signals["short"] > signals["long"]:
                self.add_to_pull(symbol, 'sell')

        time_to_sleep = random.randint(30, 180)
        time.sleep(time_to_sleep)

    def RSI_indicator(self):
        def get_rsi(symbol, interval, limit=500):
            klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
            closes = [float(entry[4]) for entry in klines]

            df = pd.DataFrame(closes, columns=["close"])
            df['rsi'] = ta.rsi(df['close'])

            return df['rsi'].iloc[-1]


        print("Checking RSI values...")

        symbols = self.get_exchange_rate_autotrading()

        for symbol in symbols:
            timeframes = ['30m', '1h', '2h', '4h', '1d']
            rsi_values = [get_rsi(symbol, tf) for tf in timeframes]

            rsi_below_30 = all(rsi <= 30 for rsi in rsi_values)
            rsi_above_70 = all(rsi >= 70 for rsi in rsi_values)
            rsi_between_30_70 = all(30 < rsi < 70 for rsi in rsi_values)

            if rsi_below_30:
                self.add_to_pull(symbol, 'buy')
            elif rsi_above_70:
                self.add_to_pull(symbol, 'sell')

        time_to_sleep = random.randint(30, 180)
        time.sleep(time_to_sleep)

    def handle(self, *args, **kwargs):
        while True:
            self.ATR_indicator()
            self.bolinger_indicator()
            self.fibonacci_indicator()
            self.moving_average_indicator()
            self.RSI_indicator()
            print("Running custom trading logic")

            time_to_sleep = random.randint(1, 5)
            time.sleep(time_to_sleep)
