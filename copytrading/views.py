from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes

from crypto.models import Crypto
from strategy.models import Strategy
from trader.models import Trader
from trader.permissions import IsSuperUser

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsSuperUser])
def get_all_stats(request):
    obj = {}
    total_deposited_money_into_strategies = Strategy.objects.aggregate(total=Sum('total_deposited'))['total']
    traders_count = Trader.objects.count()
    total_strategies_profit = Strategy.objects.aggregate(total=Sum('avg_profit'))['total']

    result = Crypto.objects.values('name').annotate(total=Sum('total_value'))
    result_dict = {item['name']: item['total'] for item in result}
    summary = sum(result_dict.values())
    for key, value in result_dict.items():
        result_dict[key] = round(value / summary * 100, 2)

    if total_strategies_profit is None:
        total_strategies_profit = 0
    else:
        total_strategies_profit /= Strategy.objects.count()

    if total_deposited_money_into_strategies is None:
        total_deposited_money_into_strategies = 0

    obj['traders_count'] = traders_count
    obj['total_deposited_money_into_strategies'] = total_deposited_money_into_strategies
    obj['total_strategies_profit'] = round(total_strategies_profit, 2)
    obj['get_all_cryptos_in_percentage'] = result_dict

    return JsonResponse(obj, safe=False)
