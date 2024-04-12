from django.db.models import Sum
from rest_framework import serializers

from crypto.models import Crypto
from strategy.models import Strategy
from strategy.serializers import StrategySerializer
from trader.models import Trader


class TraderSerializer(serializers.ModelSerializer):
    strategies = StrategySerializer(many=True, read_only=True)
    strategies_id = serializers.ListField(required=False)

    class Meta:
        model = Trader
        fields = '__all__'
        read_only_fields = ('id',)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        result = Crypto.objects.filter(strategy__trader=instance).values('name').annotate(total=Sum('total_value'))
        result_dict = {item['name']: item['total'] for item in result}

        summary = sum(result_dict.values())

        for key, value in result_dict.items():
            result_dict[key] = round(value / summary * 100, 2)

        data['get_cryptos_in_percentage'] = result_dict
        data['strategies_id'] = [strategy.id for strategy in instance.strategies.all()]
        data['profits'] = instance.profits.all().order_by('-date').values_list('value', flat=True)

        return data

    def save(self, **kwargs):
        strategies_id = self.validated_data.pop('strategies_id', None)
        instance = super().save(**kwargs)
        if strategies_id is not None:
            instance.strategies.set(Strategy.objects.filter(id__in=strategies_id))
        return instance
