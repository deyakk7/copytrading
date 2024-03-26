from django.contrib import admin

from strategy.models import Strategy, UsersInStrategy, StrategyProfitHistory, UserOutStrategy

admin.site.register(Strategy)
admin.site.register(UsersInStrategy)
admin.site.register(UserOutStrategy)
admin.site.register(StrategyProfitHistory)
