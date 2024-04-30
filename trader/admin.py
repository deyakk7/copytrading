from django.contrib import admin

from trader.models import Trader, TraderProfitHistory, TrendingThreshold

admin.site.register(Trader)
admin.site.register(TraderProfitHistory)
admin.site.register(TrendingThreshold)
