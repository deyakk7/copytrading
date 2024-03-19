from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from strategy.models import UsersInStrategy, Strategy
from .models import Trader, UsersFollowsTrader
from .permissions import IsSuperUserOrReadOnly, IsSuperUser
from .serializers import TraderSerializer, UsersFollowingsListSerializer


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


class UserFollowedList(generics.ListAPIView):
    serializer_class = UsersFollowingsListSerializer

    def get_queryset(self):
        return UsersFollowsTrader.objects.order_by('-date_of_following')[:10]


@api_view(['GET'])
@login_required()
@permission_classes([IsSuperUser])
def avg_all_strategies_profit(request):
    pass


@api_view(['POST'])
@login_required()
def follow_trader(request, trader_id):
    data = UsersFollowsTrader.objects.filter(user=request.user, trader_id=trader_id).exists()
    if data:
        return JsonResponse({'error': 'You already follow this trader.'})
    obj = UsersFollowsTrader.objects.create(user=request.user, trader_id=trader_id)
    obj.trader.followers_count += 1
    obj.trader.save()
    return JsonResponse({'success': 'You have successfully followed this trader.'})


@api_view(['DELETE'])
@login_required()
def unfollow_trader(request, trader_id):
    data = UsersFollowsTrader.objects.filter(user=request.user, trader_id=trader_id).exists()
    if not data:
        return JsonResponse({'error': 'You do not follow this trader.'})
    UsersFollowsTrader.objects.filter(user=request.user, trader_id=trader_id).delete()
    trader = Trader.objects.get(id=trader_id)
    trader.followers_count -= 1
    if trader.followers_count < 0:
        trader.followers_count = 0
    trader.save()
    return JsonResponse({'success': 'You have successfully unfollowed this trader.'})

