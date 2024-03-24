from rest_framework import serializers

from strategy.models import Strategy
from strategy.serializers import StrategySerializer
from trader.models import Trader, UsersFollowsTrader


class TraderSerializer(serializers.ModelSerializer):
    strategies = StrategySerializer(many=True, read_only=True)
    strategies_id = serializers.ListField(required=False)

    class Meta:
        model = Trader
        fields = '__all__'
        read_only_fields = ('id',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['strategies_id'] = [strategy.id for strategy in instance.strategies.all()]
        return data

    def save(self, **kwargs):
        strategies_id = self.validated_data.pop('strategies_id', None)
        instance = super().save(**kwargs)
        if strategies_id is not None:
            instance.strategies.set(Strategy.objects.filter(id__in=strategies_id))
        return instance


class UsersFollowingsListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')
    trader = serializers.CharField(source='trader.nickname')

    class Meta:
        model = UsersFollowsTrader
        fields = ['user', 'trader', 'date_of_following']
