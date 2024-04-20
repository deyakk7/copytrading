from django.db import transaction as trans
from django.db.models import Sum
from rest_framework import serializers

from crypto.models import Crypto
from strategy.models import Strategy
from strategy.serializers import StrategySerializer, StrategyDepositingSerializer
from strategy.utils import get_current_exchange_rate_usdt
from trader.models import Trader
from transaction.utils import create_open_transaction


class TraderSerializer(serializers.ModelSerializer):
    strategies = StrategySerializer(many=True, read_only=True)
    strategies_id = StrategyDepositingSerializer(many=True, required=False)

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
        data['strategies_id'] = StrategyDepositingSerializer(instance.strategies.all(), many=True).data
        data['profits'] = instance.profits.all().order_by('date').values_list('value', flat=True)

        return data

    @trans.atomic()
    def save(self, **kwargs):
        strategies_id = self.validated_data.pop('strategies_id', None)
        instance = super().save(**kwargs)

        if strategies_id is None:
            return instance

        strategies_dict = {strategy['id']: strategy['trader_deposit'] for strategy in strategies_id}

        if sum(strategies_dict.values()) > instance.deposit:
            raise serializers.ValidationError('The sum of the strategies deposit is greater than the trader deposit')

        strategy_in_db = list(Strategy.objects.filter(trader=instance).values_list('id', flat=True))
        new_id = list(set(strategies_dict.keys()) - set(strategy_in_db))

        if len(new_id) == 0:
            return instance

        exchange_rate = get_current_exchange_rate_usdt()

        crypto_from_strategies = (Crypto.objects.filter(strategy_id__in=new_id).
                                  values('strategy', 'name', 'total_value', 'side'))

        for crypto in crypto_from_strategies:
            if crypto['name'] == 'USDT':
                continue

            create_open_transaction(crypto, exchange_rate)

        if strategies_id is not None:
            instance.strategies.set(Strategy.objects.filter(id__in=strategies_dict.keys()))

            for strategy_id, deposit in strategies_dict.items():
                strategy = Strategy.objects.get(id=strategy_id)
                strategy.trader_deposit = deposit
                strategy.save()

        return instance
