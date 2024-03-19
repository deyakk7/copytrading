from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework.decorators import api_view

User = get_user_model()


@api_view(['GET'])
def ping(request):
    if request.user.is_authenticated:
        return JsonResponse({'message': 'good'}, status=200, safe=False)
    return JsonResponse({'message': 'Not authenticated'}, status=401, safe=False)
