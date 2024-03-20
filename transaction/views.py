from rest_framework import viewsets

from trader.permissions import IsSuperUser
from transaction.models import Transaction, Transfer
from transaction.serializers import TransactionSerializer, TransferSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (IsSuperUser,)


class TransferViewSet(viewsets.ModelViewSet):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = (IsSuperUser,)
