from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.viewsets import ModelViewSet

from strategy.utils import CRYPTO_NAMES, get_current_exchange_rate_pair, convert_to_usdt
from trader.permissions import IsSuperUser
from .models import Crypto
from .serializers import CryptoSerializer


class CryptoViewSet(ModelViewSet):
    queryset = Crypto.objects.all()
    serializer_class = CryptoSerializer
    permission_classes = (IsSuperUser,)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def get_exchange_info(request):
    return JsonResponse(CRYPTO_NAMES[:100], safe=False)
