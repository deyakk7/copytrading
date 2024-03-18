from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet

from strategy.tasks import CRYPTO_NAMES
from trader.permissions import IsSuperUser
from .models import Crypto
from .serializers import CryptoSerializer


class CryptoViewSet(ModelViewSet):
    queryset = Crypto.objects.all()
    serializer_class = CryptoSerializer
    permission_classes = (IsSuperUser,)


@api_view(['GET'])
def get_exchange_info(request):
    return JsonResponse(CRYPTO_NAMES[:100], safe=False)
