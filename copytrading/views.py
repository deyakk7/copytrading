from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes

from crypto.models import Crypto
from strategy.models import Strategy
from trader.models import Trader
from trader.permissions import IsSuperUser

User = get_user_model()


@api_view(['GET'])
@login_required()
@permission_classes([IsSuperUser])
def get_all_stats(request):
    obj = {}
    total_deposited_money_into_strategies = Strategy.objects.aggregate(total=Sum('total_deposited'))['total']
    traders_count = Trader.objects.count()
    total_money_in_users = User.objects.aggregate(total=Sum('wallet'))['total']
    total_strategies_profit = Strategy.objects.aggregate(total=Sum('avg_profit'))['total'] / Strategy.objects.count()

    if total_money_in_users is None:
        total_money_in_users = 0
    if total_deposited_money_into_strategies is None:
        total_deposited_money_into_strategies = 0

    obj['traders_count'] = traders_count
    obj['total_money_in_users'] = total_money_in_users
    obj['total_deposited_money_into_strategies'] = total_deposited_money_into_strategies
    obj['total_strategies_profit'] = total_strategies_profit

    return JsonResponse(obj, safe=False)
