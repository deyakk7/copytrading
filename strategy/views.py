import random

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from crypto.models import TOKENS_PAIR
from strategy.models import Strategy, UsersInStrategy
from strategy.serializers import StrategySerializer, StrategyUserSerializer
from strategy.tasks import get_current_exchange_rate
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


@api_view(['POST'])
@login_required()
def add_user_into_strategy(request, pk: int):
    input_data = request.data
    input_data['strategy'] = pk
    input_data['user'] = request.user.id
    strategy = Strategy.objects.get(id=pk)
    wallet = request.user.wallet
    if wallet < strategy.min_deposit or wallet < input_data['value']:
        return JsonResponse({"error": "Not enough money in wallet"}, status=400, safe=False)

    data = StrategyUserSerializer(data=input_data)
    if data.is_valid():
        with transaction.atomic():
            strategy.total_deposited += input_data['value']
            request.user.wallet -= input_data['value']
            strategy.save()
            request.user.save()
        data.save()
        return JsonResponse(data.data, status=201)

    return JsonResponse(data.errors, status=400)


@api_view(['DELETE'])
@login_required()
def remove_user_from_strategy(request, pk: int):
    data = UsersInStrategy.objects.filter(user=request.user, strategy_id=pk).first()
    if data is not None:
        with transaction.atomic():
            strategy = data.strategy
            strategy.total_deposited -= data.value
            request.user.wallet += data.value
            request.user.save()
            data.delete()
            strategy.save()
        transactions = random_black_box(strategy)

        return Response(transactions, status=200)
    return JsonResponse({"error": "User not found in strategy"}, status=404)


@api_view(['GET'])
@login_required()
@permission_classes([IsSuperUser])
def get_all_available_strategies(request):
    strategies = Strategy.objects.filter(trader=None)
    data = StrategySerializer(strategies, many=True).data
    return JsonResponse(data, safe=False)


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

    exchange_rate = get_current_exchange_rate()
    transactions = []
    for _ in range(count_of_transaction):
        tokens_pair = random.choice(all_tokens_list)
        amount = random.randint(10000000, 100000000) / 10000000
        price = exchange_rate[tokens_pair]
        side = bool(random.randint(0, 1))

        transaction = Transaction.objects.create(
            trader=strategy.trader,
            crypto_pair=tokens_pair,
            amount=amount,
            side=side,
            price=price,
        )
        transactions.append(TransactionSerializer(transaction).data)
    return transactions
