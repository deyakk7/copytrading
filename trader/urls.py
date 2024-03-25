from rest_framework.routers import SimpleRouter

from .views import TraderViewSet

router = SimpleRouter()
router.register(r'', TraderViewSet)

urlpatterns = []

urlpatterns += router.urls
