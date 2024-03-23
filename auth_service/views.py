from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes

from trader.permissions import IsSuperUser

User = get_user_model()


@api_view(['GET'])
def ping(request):
    if request.user.is_authenticated:
        return JsonResponse({'message': 'good'}, status=200, safe=False)
    return JsonResponse({'message': 'Not authenticated'}, status=401, safe=False)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def users_stats(request):
    obj = {}
    total_money_in_users = User.objects.aggregate(total=Sum('wallet'))['total']
    if total_money_in_users is None:
        total_money_in_users = 0

    total_users_count = User.objects.filter(is_superuser=False).count()

    obj['total_money_in_users'] = total_money_in_users
    obj['total_users_count'] = total_users_count

    return JsonResponse(obj, safe=False)