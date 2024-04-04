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


@api_view(['GET'])
@permission_classes([IsSuperUser])
def get_all_cryptos_in_percentage(request):
    result = Crypto.objects.values('name').annotate(total=Sum('total_value'))
    result_dict = {item['name']: item['total'] for item in result}
    summary = sum(result_dict.values())
    for key, value in result_dict.items():
        result_dict[key] = round(value / summary * 100, 4)

    return JsonResponse(result_dict, safe=False)
