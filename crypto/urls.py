from rest_framework.routers import DefaultRouter

from .views import CryptoViewSet

router = DefaultRouter()
router.register(r'', CryptoViewSet)

urlpatterns = router.urls
