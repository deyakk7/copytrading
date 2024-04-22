import decimal
import random

from crypto.models import Crypto
from strategy.utils import get_percentage_change
from transaction.models import TransactionClose, TransactionOpen


def create_open_transaction(crypto_data: Crypto, exchange_rate: dict[str, decimal.Decimal]):
    if crypto_data.name == 'USDT':
        return

    strategy = crypto_data.strategy
    crypto_pair = crypto_data.name + "USDT"
    side = crypto_data.side
    open_price = exchange_rate[crypto_data.name]
    total_value = crypto_data.total_value

    current_pool_money = crypto_data.strategy.available_pool

    value = ((total_value / 100) * current_pool_money) / open_price

    return TransactionOpen.objects.create(
        strategy=strategy,
        crypto_pair=crypto_pair,
        side=side,
        open_price=open_price,
        percentage=total_value,
        value=value
    )


def create_close_transaction(transaction_data: TransactionOpen, exchange_rate: dict[str, decimal.Decimal]):

    strategy = transaction_data.strategy
    crypto_pair = transaction_data.crypto_pair
    side = transaction_data.side
    open_price = transaction_data.open_price
    open_time = transaction_data.open_time
    close_price = exchange_rate[crypto_pair[:-4]]
    percentage = transaction_data.percentage
    value = transaction_data.value

    percentage_change = get_percentage_change(crypto_pair[:-4], open_price, exchange_rate)

    income = transaction_data.value * close_price
    costs = transaction_data.value * open_price

    roi = ((income - costs) / costs) * 100

    saved_profit = (percentage / 100) * percentage_change

    TransactionClose.objects.create(
        strategy=strategy,
        crypto_pair=crypto_pair,
        side=side,
        open_price=open_price,
        close_price=close_price,
        percentage=percentage,
        value=value,
        roi=roi,
        open_time=open_time
    )

    strategy.saved_avg_profit += saved_profit
    strategy.save()


def averaging_open_transaction(crypto_db: Crypto, transaction_op: TransactionOpen, exchange_rate):

    current_available_pool = transaction_op.strategy.available_pool
    money = ((crypto_db.total_value - transaction_op.percentage) / 100) * current_available_pool

    value = money / exchange_rate[crypto_db.name]
    total_sum_value = value + transaction_op.value

    old_percentage_crypto = float(transaction_op.value) / float(total_sum_value)
    new_percentage_crypto = float(value) / float(total_sum_value)

    new_open_price = old_percentage_crypto * transaction_op.value + new_percentage_crypto * value

    transaction_op.open_price = decimal.Decimal(new_open_price)
    transaction_op.value += value

    transaction_op.save()
