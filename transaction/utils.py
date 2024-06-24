import decimal

from crypto.models import Crypto
from strategy.utils import get_percentage_change
from transaction.models import TransactionClose, TransactionOpen


def create_open_transaction(crypto_data: Crypto, exchange_rate: dict[str, decimal.Decimal], percentage_from_pool):
    if crypto_data.name == 'USDT':
        return

    strategy = crypto_data.strategy
    crypto_pair = crypto_data.name + "USDT"
    side = crypto_data.side
    open_price = exchange_rate[crypto_data.name]
    total_value = crypto_data.total_value

    available_pool = strategy.available_pool

    money = (percentage_from_pool / 100) * available_pool

    value = money / open_price

    return TransactionOpen.objects.create(
        strategy=strategy,
        crypto_pair=crypto_pair,
        side=side,
        open_price=open_price,
        percentage=total_value,
        value=value
    ), money


def create_close_transaction(transaction_data: TransactionOpen, exchange_rate: dict[str, decimal.Decimal], to_close_per):
    strategy = transaction_data.strategy
    crypto_pair = transaction_data.crypto_pair
    side = transaction_data.side
    open_price = transaction_data.open_price
    open_time = transaction_data.open_time
    close_price = exchange_rate[crypto_pair[:-4]]

    open_percentage = transaction_data.percentage * (to_close_per / 100)
    close_percentage = transaction_data.percentage - open_percentage

    open_value = transaction_data.value * (to_close_per / 100)
    close_value = transaction_data.value - open_value

    percentage_change = get_percentage_change(crypto_pair[:-4], open_price, exchange_rate)

    income = close_value * close_price
    costs = close_value * open_price

    roi = ((income - costs) / costs) * 100
    roi = -roi if side == 'short' else roi

    saved_profit = (to_close_per / 100) * percentage_change

    saved_profit = -saved_profit if side == 'short' else saved_profit

    TransactionClose.objects.create(
        strategy=strategy,
        crypto_pair=crypto_pair,
        side=side,
        open_price=open_price,
        close_price=close_price,
        percentage=close_percentage,
        value=close_value,
        roi=roi,
        open_time=open_time
    )

    transaction_data.value = open_value
    transaction_data.percentage = open_percentage
    transaction_data.save()

    strategy.available_pool += close_price * close_value
    strategy.saved_avg_profit += saved_profit
    strategy.save()


def averaging_open_transaction(crypto_db: Crypto, transaction_op: TransactionOpen, exchange_rate, percentage_from_pool):
    current_available_pool = transaction_op.strategy.available_pool
    money = (percentage_from_pool / 100) * current_available_pool

    value = money / exchange_rate[crypto_db.name]
    total_sum_value = value + transaction_op.value

    new_open_price = (transaction_op.open_price * transaction_op.value + exchange_rate[
        transaction_op.crypto_pair[:-4]] * value) / total_sum_value

    transaction_op.open_price = decimal.Decimal(new_open_price)
    transaction_op.value += value

    transaction_op.save()

    return money


def calculate_roi(transactions: TransactionOpen, exchange_rate: dict[str, decimal.Decimal]):
    open_price = transactions.open_price
    close_price = exchange_rate[transactions.crypto_pair[:-4]]

    close_value = transactions.value

    income = close_value * close_price
    costs = close_value * open_price

    roi = ((income - costs) / costs) * 100
    roi = -roi if transactions.side == 'short' else roi

    return roi
