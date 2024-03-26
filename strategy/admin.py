from django.contrib import admin

from strategy.models import Strategy, UsersInStrategy, StrategyProfitHistory

admin.site.register(Strategy)
admin.site.register(UsersInStrategy)
admin.site.register(StrategyProfitHistory)
