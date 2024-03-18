from rest_framework import serializers

from strategy.serializers import StrategySerializer
from trader.models import Trader


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
