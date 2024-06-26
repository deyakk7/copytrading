from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import GetListUsers, GetUserBalance

router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('ping/', views.ping, name='ping'),
    path('is_admin/', views.is_superuser, name='is_superuser'),
    path('users_stats/', views.users_stats, name='users_stats'),
    path('', include('djoser.urls.authtoken')),

    path('get_users_list/', GetListUsers.as_view(), name='get_users_list'),
    path('get_user_balance/', GetUserBalance.as_view(), name='get_user_balance'),
]

urlpatterns += router.urls
