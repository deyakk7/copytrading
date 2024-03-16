from rest_framework.routers import DefaultRouter

from transaction.views import TransactionViewSet

router = DefaultRouter()
router.register(r'', TransactionViewSet)

urlpatterns = router.urls
