from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('schema', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('admin/', admin.site.urls),
    path('traders/', include('trader.urls')),
    path('strategies/', include('strategy.urls')),
    path('crypto/', include('crypto.urls')),
    path('transactions/', include('transaction.urls')),
    path('copytrading/', include('copytrading.urls')),
    path('auth/', include('auth_service.urls')),
]
