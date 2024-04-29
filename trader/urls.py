from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import TraderViewSet, TrendingThresholdView

router = SimpleRouter()
router.register(r'', TraderViewSet)

urlpatterns = [
    path('tranding-threshold/', TrendingThresholdView.as_view(), name='trending-threshold'),
]

urlpatterns += router.urls
