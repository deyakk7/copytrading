from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CryptoViewSet, get_exchange_info

router = DefaultRouter()
router.register(r'', CryptoViewSet)

urlpatterns = [
    path('get_exchange_info/', get_exchange_info, name='get_exchange_info'),
]

urlpatterns += router.urls
