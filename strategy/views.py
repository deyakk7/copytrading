import decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db import transaction as trans
from django.http import JsonResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from strategy.models import Strategy, UsersInStrategy, UserOutStrategy
from strategy.serializers import StrategySerializer, StrategyUserSerializer, StrategyUserListSerializer, \
    UserCopingStrategySerializer, StrategyCustomProfitSerializer, UserOutStrategySerializer
from trader.permissions import IsSuperUserOrReadOnly, IsSuperUser
from transaction.models import TransactionOpen, TransactionClose


class StrategyViewSet(ModelViewSet):
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = (IsSuperUserOrReadOnly,)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        users = UsersInStrategy.objects.filter(strategy=instance).exists()
        if users:
            return JsonResponse({'error': 'You cannot delete this strategy because it has users.'})
        self.perform_destroy(instance)
        return Response(status=204)

    @action(detail=False, methods=['get'])
    def my(self, request, *args, **kwargs):
        my_strategies = UsersInStrategy.objects.filter(user=request.user).values_list('strategy', flat=True).distinct()
        return JsonResponse({'my_copied_strategies_id': list(my_strategies)}, safe=False)

    @action(detail=False, methods=['get'])
    def my_deposited(self, request, *args, **kwargs):
        my_strategies = UsersInStrategy.objects.filter(user=request.user)

        data = []
        for strategy in my_strategies:
            data.append({
                'strategy_id': strategy.strategy_id,
                'value': strategy.value,
                'profit': strategy.profit,
                'date_of_adding': strategy.date_of_adding,
            })

        return JsonResponse(data, safe=False)

    @action(detail=True, methods=['get'])
    def opened_transactions(self, request, *args, **kwargs):

        transactions = TransactionOpen.objects.filter(strategy=self.get_object())
        data = []
        for transaction_db in transactions:
            data.append(
                {
                    "id": transaction_db.id,
                    "crypto_pair": transaction_db.crypto_pair,
                    "open_price": transaction_db.open_price,
                    "open_time": transaction_db.open_time,
                    "total_value": transaction_db.total_value,
                    "side": transaction_db.side
                }
            )
        return JsonResponse(data, status=200, safe=False)

    @action(detail=True, methods=['get'])
    def closed_transactions(self, request, *args, **kwargs):
        transactions = TransactionClose.objects.filter(strategy=self.get_object())
        data = []

        for transaction_db in transactions:
            data.append(
                {
                    "id": transaction_db.id,
                    "crypto_pair": transaction_db.crypto_pair,
                    "open_price": transaction_db.open_price,
                    "close_price": transaction_db.close_price,
                    "close_time": transaction_db.close_time,
                    "roi": transaction_db.roi,
                    "total_value": transaction_db.total_value,
                    "side": transaction_db.side,
                }
            )

        return JsonResponse(data, status=200, safe=False)


class UsersCopiedListView(generics.ListAPIView):
    serializer_class = StrategyUserListSerializer
    permission_classes(IsSuperUser, )

    def get_queryset(self):
        return UsersInStrategy.objects.order_by('-date_of_adding')[:10]


class UsersOutStrategyListView(generics.ListAPIView):
    serializer_class = UserOutStrategySerializer
    permission_classes(IsSuperUser, )

    def get_queryset(self):
        return UserOutStrategy.objects.order_by('-date_of_out')[:10]


@extend_schema(
    request=UserCopingStrategySerializer,
)
@api_view(['POST'])
@login_required()
def add_user_into_strategy(request, pk: int):
    if request.user.is_superuser:
        return JsonResponse({"error": "Superuser cannot copy strategies"}, status=400)
    wallet = request.user.wallet

    input_data = request.data
    input_data['strategy'] = pk
    input_data['user'] = request.user.id

    strategy = Strategy.objects.get(id=pk)

    if strategy.trader is None:
        return JsonResponse({"error": "This strategy is not available"}, status=400, safe=False)

    current_available_copiers = strategy.trader.max_copiers - strategy.trader.copiers_count

    if not current_available_copiers:
        return JsonResponse({"error": "This trader is full"}, status=400, safe=False)

    if wallet < strategy.min_deposit or wallet < decimal.Decimal(input_data['value']):
        return JsonResponse({"error": "Not enough money in wallet"}, status=400, safe=False)

    input_data['different_profit_from_strategy'] = strategy.avg_profit

    data = StrategyUserSerializer(data=input_data)
    if data.is_valid():
        strategy.total_deposited += decimal.Decimal(input_data['value'])
        request.user.wallet -= decimal.Decimal(input_data['value'])

        strategy.total_copiers += 1
        strategy.trader.copiers_count += 1

        with transaction.atomic():
            strategy.trader.save()
            strategy.save()
            request.user.save()

            data.save()

        return JsonResponse(data.data, status=201)

    return JsonResponse(data.errors, status=400)


@api_view(['DELETE'])
@login_required()
def remove_user_from_strategy(request, pk: int):
    data: UsersInStrategy = UsersInStrategy.objects.filter(user=request.user, strategy_id=pk).first()
    if data is None:
        return JsonResponse({"error": "User not found in strategy"}, status=404)

    strategy = data.strategy
    strategy.total_deposited -= data.value

    if strategy.total_copiers > 0:
        strategy.total_copiers -= 1
    if strategy.trader.copiers_count > 0:
        strategy.trader.copiers_count -= 1

    request.user.wallet += data.value + data.profit * (data.value / decimal.Decimal(100))

    with transaction.atomic():
        UserOutStrategy.objects.create(
            user=data.user,
            strategy=data.strategy,
            value=data.value,
            profit=data.profit,
            date_of_adding=data.date_of_adding,
            date_of_out=timezone.now()
        )

        request.user.save()

        strategy.save()
        strategy.trader.save()

        data.delete()

    return JsonResponse({"message": "You have left the strategy successfully"}, status=200)


class StrategyAvailableListView(generics.ListAPIView):
    serializer_class = StrategySerializer
    permission_classes(IsSuperUser, )

    def get_queryset(self):
        return Strategy.objects.filter(trader=None)


@extend_schema(
    request=StrategyCustomProfitSerializer,
)
@permission_classes([IsSuperUser])
@api_view(['POST'])
def change_avg_profit(request, pk: int):
    strategy = get_object_or_404(Strategy, pk=pk)

    data = StrategyCustomProfitSerializer(data=request.data)
    if data.is_valid():
        if strategy.current_custom_profit != 0:
            return JsonResponse({"error": "already changing custom avg profit need to wait"}, status=400)

        new_custom_profit = data.validated_data['new_percentage_change_profit']
        with trans.atomic():
            strategy.avg_profit += new_custom_profit
            strategy.custom_avg_profit += new_custom_profit
            users = UsersInStrategy.objects.filter(strategy=strategy)
            for user in users:
                user.profit += new_custom_profit
                user.save()
            strategy.save()

        return JsonResponse({"message": "changed"}, status=200)
    return JsonResponse(data.errors, status=400)
