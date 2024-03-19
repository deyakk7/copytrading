from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import TraderViewSet, follow_trader, unfollow_trader, UserFollowedList

router = SimpleRouter()
router.register(r'', TraderViewSet)

urlpatterns = [
    path('follow/<int:trader_id>/', follow_trader, name='follow_trader'),
    path('unfollow/<int:trader_id>/', unfollow_trader, name='unfollow_trader'),
    path('last_followed_traders/', UserFollowedList.as_view(), name='last_followed_traders'),
]

urlpatterns += router.urls
