from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import StrategyViewSet, add_user_into_strategy, remove_user_from_strategy

router = DefaultRouter()
router.register(r'', StrategyViewSet)

urlpatterns = [
    path('add/<int:pk>/', add_user_into_strategy, name='add_user_into_strategy'),
    path('remove/<int:pk>/', remove_user_from_strategy, name='remove_user_from_strategy')
]

urlpatterns += router.urls
