from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CryptoViewSet, get_exchange_info, get_all_cryptos_in_percentage

router = DefaultRouter()
router.register(r'', CryptoViewSet)

urlpatterns = [
    path('get_exchange_info/', get_exchange_info, name='get_exchange_info'),
    path('get_all_cryptos_in_percentage/', get_all_cryptos_in_percentage, name='get_all_cryptos_in_percentage')
]

urlpatterns += router.urls
