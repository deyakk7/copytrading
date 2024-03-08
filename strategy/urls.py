from rest_framework.routers import DefaultRouter

from .views import StrategyViewSet

router = DefaultRouter()
router.register(r'', StrategyViewSet)

urlpatterns = router.urls
