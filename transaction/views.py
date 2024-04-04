import random

from rest_framework import viewsets

from crypto.models import TOKENS_PAIR
from strategy.utils import get_current_exchange_rate_pair
from trader.permissions import IsSuperUser
from transaction.models import Transaction, Transfer, UserDeposit
from transaction.serializers import TransactionSerializer, TransferSerializer, UserDepositSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (IsSuperUser,)


class TransferViewSet(viewsets.ModelViewSet):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = (IsSuperUser,)


class UserDepositViewSet(viewsets.ModelViewSet):
    queryset = UserDeposit.objects.all()
    serializer_class = UserDepositSerializer
    permission_classes = (IsSuperUser,)


def random_black_box(strategy):
    count_of_transaction = random.randint(3, 6)
    cryptos = [x.name for x in strategy.crypto.all()]
    all_tokens_list = [i + "USDT" for i in cryptos if i + "USDT" in TOKENS_PAIR]

    for i in range(len(cryptos)):
        for j in range(i + 1, len(cryptos)):
            f, s = cryptos[i], cryptos[j]
            if f + s in TOKENS_PAIR:
                all_tokens_list.append(f + s)
            elif s + f in TOKENS_PAIR:
                all_tokens_list.append(s + f)

    exchange_rate = get_current_exchange_rate_pair()
    transactions = []
    for _ in range(count_of_transaction):
        tokens_pair = random.choice(all_tokens_list)
        amount = random.randint(10000000, 100000000) / 10000000
        price = exchange_rate[tokens_pair]
        side = bool(random.randint(0, 1))

        transaction_obj = Transaction.objects.create(
            trader=strategy.trader,
            crypto_pair=tokens_pair,
            amount=amount,
            side=side,
            price=price,
        )
        transactions.append(TransactionSerializer(transaction_obj).data)
    return transactions
