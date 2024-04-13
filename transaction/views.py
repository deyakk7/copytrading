from rest_framework import viewsets

from trader.permissions import IsSuperUser
from transaction.models import TransactionClose, Transfer, UserDeposit
from transaction.serializers import TransactionSerializer, TransferSerializer, UserDepositSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = TransactionClose.objects.all()
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
