from rest_framework import serializers

from strategy.serializers import StrategySerializer
from trader.models import Trader, UsersFollowsTrader


class TraderSerializer(serializers.ModelSerializer):
    strategies = StrategySerializer(many=True, required=False)

    class Meta:
        model = Trader
        fields = '__all__'
        read_only_fields = ('id',)

    def create(self, validated_data):
        strategies_data = validated_data.pop('strategies', None)
        trader = Trader.objects.create(**validated_data)

        if strategies_data is None:
            return trader

        for strategy_data in strategies_data:
            strategy_data['trader'] = trader
            StrategySerializer.create(StrategySerializer(), validated_data=strategy_data)
        return trader

    def update(self, instance, validated_data):
        strategies_data = validated_data.pop('strategies', None)
        instance.nickname = validated_data.get('nickname', instance.nickname)
        instance.about = validated_data.get('about', instance.about)
        instance.photo = validated_data.get('photo', instance.photo)
        instance.followers_count = validated_data.get('followers_count', instance.followers_count)
        instance.copiers_count = validated_data.get('copiers_count', instance.copiers_count)
        instance.profit_to_loss_ratio = validated_data.get('profit_to_loss_ratio', instance.profit_to_loss_ratio)
        instance.weekly_trades = validated_data.get('weekly_trades', instance.weekly_trades)
        instance.avg_holding_time = validated_data.get('avg_holding_time', instance.avg_holding_time)
        instance.roi_volatility = validated_data.get('roi_volatility', instance.roi_volatility)
        instance.sharpe_ratio = validated_data.get('sharpe_ratio', instance.sharpe_ratio)
        instance.sortino_ratio = validated_data.get('sortino_ratio', instance.sortino_ratio)
        instance.last_traded_at = validated_data.get('last_traded_at', instance.last_traded_at)

        instance.save()

        if strategies_data is None:
            return instance

        keep_strategies = []
        for strategy_data in strategies_data:
            strategy_data['trader'] = instance
            s = StrategySerializer.create(StrategySerializer(), validated_data=strategy_data)
            keep_strategies.append(s.id)

        for strategy in instance.strategies.all():
            if strategy.id not in keep_strategies:
                strategy.delete()

        return instance


class UsersFollowingsListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')
    trader = serializers.CharField(source='trader.nickname')

    class Meta:
        model = UsersFollowsTrader
        fields = ['user', 'trader', 'date_of_following']
