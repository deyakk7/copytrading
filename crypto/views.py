from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet

from trader.permissions import IsSuperUser
from .models import Crypto, TOKENS_PAIR
from .serializers import CryptoSerializer


class CryptoViewSet(ModelViewSet):
    queryset = Crypto.objects.all()
    serializer_class = CryptoSerializer
    permission_classes = (IsSuperUser,)


@api_view(['GET'])
def get_exchange_info(request):
    return JsonResponse(TOKENS_PAIR, safe=False)
