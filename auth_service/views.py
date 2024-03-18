from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model

from trader.permissions import IsSuperUser


User = get_user_model()

@api_view(['GET'])
def ping(request):
    if request.user.is_authenticated:
        return JsonResponse({'message': 'good'}, status=200, safe=False)
    return JsonResponse({'message': 'Not authenticated'}, status=401, safe=False)


@api_view(['GET'])
@login_required()
@permission_classes([IsSuperUser])
def all_users_money(request):
    total_wallet_sum = User.objects.aggregate(total=Sum('wallet'))['total']
    if total_wallet_sum is None:
        total_wallet_sum = 0
    return JsonResponse({'total_wallet_sum': total_wallet_sum}, status=200, safe=False)
