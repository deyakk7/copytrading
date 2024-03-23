from django.urls import path

from . import views

urlpatterns = [
    path('ping/', views.ping, name='ping'),
    path('users_stats/', views.users_stats, name='users_stats'),
]
