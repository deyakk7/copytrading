from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from strategy.models import UsersInStrategy
from .models import Trader
from .permissions import IsSuperUserOrReadOnly
from .serializers import TraderSerializer


class TraderViewSet(ModelViewSet):
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    permission_classes = (IsSuperUserOrReadOnly,)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        users = UsersInStrategy.objects.filter(strategy__trader=instance).exists()
        if users:
            return JsonResponse({'error': 'You cannot delete this trader because it has users.'})
        self.perform_destroy(instance)
        return Response(status=204)

    @action(detail=False, methods=['get'])
    def my(self, request, *args, **kwargs):
        my_traders = UsersInStrategy.objects.filter(user=request.user).values_list('strategy__trader',
                                                                                   flat=True).distinct()
        return JsonResponse({'my_traders_copied_id': list(my_traders)}, safe=False)
