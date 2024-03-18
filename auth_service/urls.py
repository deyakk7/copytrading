from django.urls import path

from . import views

urlpatterns = [
    path('ping/', views.ping, name='ping'),
    path('all_users_money/', views.all_users_money, name='all_users_money'),
]
