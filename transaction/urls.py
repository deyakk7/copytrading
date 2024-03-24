from rest_framework.routers import DefaultRouter

from transaction.views import TransactionViewSet, TransferViewSet

router = DefaultRouter()
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'', TransactionViewSet)
router.register(r'user-deposit', TransactionViewSet, basename='user-deposit')

urlpatterns = router.urls
