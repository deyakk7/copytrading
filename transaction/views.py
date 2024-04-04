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
