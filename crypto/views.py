from rest_framework.viewsets import ModelViewSet

from trader.permissions import IsSuperUser
from .models import Crypto
from .serializers import CryptoSerializer


class CryptoViewSet(ModelViewSet):
    queryset = Crypto.objects.all()
    serializer_class = CryptoSerializer
    permission_classes = (IsSuperUser,)
