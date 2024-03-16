from rest_framework.viewsets import ModelViewSet

from .models import Trader
from .permissions import IsSuperUserOrReadOnly
from .serializers import TraderSerializer


class TraderViewSet(ModelViewSet):
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    permission_classes = (IsSuperUserOrReadOnly,)
