from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.viewsets import ModelViewSet

from .models import Trader
from .serializers import TraderSerializer
from . permissions import IsSuperUser


class TraderViewSet(ModelViewSet):
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    permission_classes = (IsSuperUser, )
    authentication_classes = (SessionAuthentication, BasicAuthentication)
