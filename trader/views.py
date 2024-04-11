from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from strategy.models import UsersInStrategy
from transaction.serializers import TransactionSerializer
from .models import Trader
from .permissions import IsSuperUserOrReadOnly
from .serializers import TraderSerializer


class TraderViewSet(ModelViewSet):
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    permission_classes = (IsSuperUserOrReadOnly,)

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(visible=True)

        return queryset

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

    @extend_schema(
        responses=TransactionSerializer(many=True),
    )
    @action(detail=True, methods=['get'])
    def transactions(self, request, *args, **kwargs):
        trader = self.get_object()
        transactions = trader.transaction_set.all().order_by('-close_time')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_stats(self, request, *args, **kwargs):
        trader = self.get_object()
        return JsonResponse(trader.get_stats(), safe=False)