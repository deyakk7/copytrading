from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import JsonResponse
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_service.utils import get_user_info, get_user_balance_info
from trader.permissions import IsSuperUser

User = get_user_model()


class UserViewSet(BaseUserViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_superuser=False)


@api_view(['GET'])
def ping(request):
    if request.user.is_authenticated:
        return JsonResponse({'message': 'good'}, status=200, safe=False)
    return JsonResponse({'message': 'Not authenticated'}, status=401, safe=False)


@api_view(['GET'])
def is_superuser(request):
    if request.user.is_authenticated:
        return JsonResponse({'is_admin': request.user.is_superuser}, safe=False)
    return JsonResponse({'error': "Not authenticated"}, status=401, safe=False)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def users_stats(request):
    obj = {}
    total_users_balance = User.objects.filter(is_superuser=False).aggregate(total=Sum('wallet'))['total']
    total_users_count = User.objects.filter(is_superuser=False).count()

    obj['total_users_balance'] = round(total_users_balance, 2)
    obj['total_users_count'] = total_users_count

    return JsonResponse(obj, safe=False)


class GetListUsers(APIView):
    # permission_classes = [IsSuperUser]

    def get(self, request):
        response_data = get_user_info()
        print(response_data)
        print(response_data.json())
        return Response(response_data.json())


class GetUserBalance(APIView):

    def get(self, request):

        internal_id = request.query_params.get('internal_id')
        payload = {
            'internal_id': internal_id
        }
        response_data = get_user_balance_info(payload)

        return Response(response_data.json())
