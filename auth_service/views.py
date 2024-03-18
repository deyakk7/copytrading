from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework.decorators import api_view


@api_view(['GET'])
def ping(request):
    if request.user.is_authenticated:
        return JsonResponse({'message': 'good'}, status=200, safe=False)

    return JsonResponse({'message': 'Not authenticated'}, status=401, safe=False)
