import decimal
import random

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from crypto.models import TOKENS_PAIR, CryptoInUser
from strategy.models import Strategy, UsersInStrategy, UserOutStrategy
from strategy.serializers import StrategySerializer, StrategyUserSerializer, StrategyUserListSerializer, \
    UserCopingStrategySerializer, StrategyCustomProfitSerializer, UserOutStrategySerializer
from strategy.tasks import change_custom_profit
from strategy.utils import get_current_exchange_rate_pair, get_current_exchange_rate_usdt
from trader.permissions import IsSuperUserOrReadOnly, IsSuperUser
from transaction.models import Transaction
from transaction.serializers import TransactionSerializer


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
    input_data = request.data
    input_data['strategy'] = pk
    input_data['user'] = request.user.id
    strategy = Strategy.objects.get(id=pk)
    wallet = request.user.wallet
    if strategy.trader is None:
        return JsonResponse({"error": "This strategy is not available"}, status=400, safe=False)
    if strategy.total_copiers >= strategy.max_users:
        return JsonResponse({"error": "This strategy is full"}, status=400, safe=False)
    if wallet < strategy.min_deposit or wallet < decimal.Decimal(input_data['value']):
        return JsonResponse({"error": "Not enough money in wallet"}, status=400, safe=False)
    input_data['current_custom_profit'] = strategy.current_custom_profit
    input_data['custom_profit'] = strategy.custom_avg_profit

    data = StrategyUserSerializer(data=input_data)
    if data.is_valid():
        with transaction.atomic():
            strategy.total_deposited += decimal.Decimal(input_data['value'])
            request.user.wallet -= decimal.Decimal(input_data['value'])
            strategy.total_copiers = strategy.users.count() + 1
            strategy.trader.copiers_count += 1
            strategy.save()
            request.user.save()
        obj = data.save()
        crypto_in_strategy = obj.strategy.crypto.all()
        exchange_rate = get_current_exchange_rate_usdt()
        for crypto in crypto_in_strategy:
            CryptoInUser.objects.create(
                name=crypto.name,
                exchange_rate=exchange_rate[crypto.name],
                total_value=crypto.total_value,
                user_in_strategy=obj
            )

        return JsonResponse(data.data, status=201)

    return JsonResponse(data.errors, status=400)


@api_view(['DELETE'])
@login_required()
def remove_user_from_strategy(request, pk: int):
    data = UsersInStrategy.objects.filter(user=request.user, strategy_id=pk).first()
    if data is not None:
        strategy = data.strategy
        with transaction.atomic():
            strategy.total_deposited -= data.value
            strategy.total_copiers = strategy.users.count()
            strategy.trader.copiers_count -= 1
            if strategy.trader.copiers_count == 0:
                strategy.trader.copiers_count = 0
            request.user.wallet += data.value + data.profit * (data.value / decimal.Decimal(100))
            request.user.save()
            UserOutStrategy.objects.create(
                user=data.user,
                strategy=data.strategy,
                value=data.value,
                profit=data.profit,
                date_of_adding=data.date_of_adding,
                date_of_out=timezone.now()
            )

            data.delete()
            strategy.save()
        transactions = random_black_box(strategy)

        return Response(transactions, status=200)
    return JsonResponse({"error": "User not found in strategy"}, status=404)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def get_all_available_strategies(request):
    strategies = Strategy.objects.filter(trader=None)
    data = StrategySerializer(strategies, many=True).data
    return JsonResponse(data, safe=False)


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
        change_custom_profit.delay(pk, data.data)
        return JsonResponse({"message": "sure"}, status=200)
    return JsonResponse(data.errors, status=400)


def random_black_box(strategy):
    count_of_transaction = random.randint(3, 6)
    cryptos = [x.name for x in strategy.crypto.all()]
    all_tokens_list = [i + "USDT" for i in cryptos if i + "USDT" in TOKENS_PAIR]

    for i in range(len(cryptos)):
        for j in range(i + 1, len(cryptos)):
            f, s = cryptos[i], cryptos[j]
            if f + s in TOKENS_PAIR:
                all_tokens_list.append(f + s)
            elif s + f in TOKENS_PAIR:
                all_tokens_list.append(s + f)

    exchange_rate = get_current_exchange_rate_pair()
    transactions = []
    for _ in range(count_of_transaction):
        tokens_pair = random.choice(all_tokens_list)
        amount = random.randint(10000000, 100000000) / 10000000
        price = exchange_rate[tokens_pair]
        side = bool(random.randint(0, 1))

        transaction_obj = Transaction.objects.create(
            trader=strategy.trader,
            crypto_pair=tokens_pair,
            amount=amount,
            side=side,
            price=price,
        )
        transactions.append(TransactionSerializer(transaction_obj).data)
    return transactions
