from django.urls import path

from . import views

urlpatterns = [
    path('stats/', views.get_all_stats, name='get_all_stats')
]