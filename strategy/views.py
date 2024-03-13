from django.http import HttpResponse
from rest_framework.viewsets import ModelViewSet

from strategy.models import Strategy
from strategy.serializers import StrategySerializer
from trader.permissions import IsSuperUser


class StrategyViewSet(ModelViewSet):
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = (IsSuperUser,)


def test_func(request):

    return HttpResponse("good")
