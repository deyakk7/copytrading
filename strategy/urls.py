from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'', views.StrategyViewSet)

urlpatterns = [
    path('add/<int:pk>/', views.add_user_into_strategy, name='add_user_into_strategy'),
    path('remove/<int:pk>/', views.remove_user_from_strategy, name='remove_user_from_strategy'),
    path('list_available_strategies/', views.get_all_available_strategies, name='list_available_strategies'),
    path('last_deposited_users/', views.UsersCopiedListView.as_view(), name='last_deposited_users'),
    path('change_avg_profit/<int:pk>/', views.change_avg_profit, name='change_avg_profit'),
    path('last_out_users/', views.UsersOutStrategyListView.as_view(), name='last_out_users'),
]

urlpatterns += router.urls
