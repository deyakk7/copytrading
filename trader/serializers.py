from django.db import transaction as trans
from django.db.models import Sum, FloatField, F, ExpressionWrapper, Count
from django.db.models.functions import Cast
from rest_framework import serializers

from crypto.models import Crypto
from strategy.models import Strategy
from strategy.serializers import StrategySerializer, StrategyDepositingSerializer
from strategy.utils import get_current_exchange_rate_usdt
from trader.models import Trader, TrendingThreshold
from transaction.models import TransactionOpen
from transaction.utils import create_open_transaction


class TraderSerializer(serializers.ModelSerializer):
    strategies = StrategySerializer(many=True, read_only=True)
    strategies_id = StrategyDepositingSerializer(many=True, required=False)
    copiers_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Trader
        fields = '__all__'
        read_only_fields = ('id',)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['strategies_id'] = StrategyDepositingSerializer(instance.strategies.all(), many=True).data
        data['profits'] = instance.profits.all().order_by('date')[-100:].values_list('value', flat=True)

        total_value_sum = Crypto.objects.filter(strategy__trader=instance).aggregate(total_sum=Sum('total_value'))

        if total_value_sum['total_sum'] is None:
            return data

        total_value_sum = float(total_value_sum['total_sum'])

        crypto_values = Crypto.objects.filter(strategy__trader=instance).values('name', 'side') \
            .annotate(total_value_group=Sum('total_value')) \
            .annotate(percentage=ExpressionWrapper(
                Cast(F('total_value_group'), FloatField()) / total_value_sum * 100,
                output_field=FloatField()
            ))

        result_dict = [
            {
                'name': crypto['name'],
                'side': 'L' if crypto['side'] == 'long' else 'S',
                'percentage': round(crypto['percentage'], 2)
            }
            for crypto in crypto_values
        ]

        data['get_cryptos_in_percentage'] = result_dict

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

        instance.strategies.set(Strategy.objects.filter(id__in=strategies_dict.keys()))

        for strategy_id, deposit in strategies_dict.items():
            strategy = Strategy.objects.get(id=strategy_id)
            strategy.trader_deposit = deposit
            strategy.available_pool = deposit

            strategy.save()

        exchange_rate = get_current_exchange_rate_usdt()

        crypto_from_strategies = Crypto.objects.filter(strategy_id__in=new_id)

        for crypto in crypto_from_strategies:
            if crypto.name == 'USDT':
                continue

            create_open_transaction(crypto, exchange_rate, crypto.total_value)

        for st_id in new_id:
            transactions = TransactionOpen.objects.filter(
                strategy_id=st_id
            )
            if len(transactions) == 0:
                continue

            sum_of_money = 0
            percentage_value = 0

            for transaction_op in transactions:
                sum_of_money += transaction_op.open_price * transaction_op.value
                percentage_value += transaction_op.percentage

            strategy_db: Strategy = Strategy.objects.filter(id=st_id).first()
            strategy_db.available_pool = (sum_of_money * (100 - percentage_value)) / percentage_value
            strategy_db.save()

        instance.available_deposit = instance.deposit - sum(strategies_dict.values())
        instance.save()

        return instance

    def update(self, instance, validated_data):
        max_copiers = validated_data.pop('max_copiers', None)

        total_copiers = Strategy.objects.filter(trader=instance).aggregate(
            count_copiers=Count('total_copiers')
        )['count_copiers']
        if max_copiers is not None:
            if total_copiers is None or max_copiers > total_copiers:
                validated_data['max_copiers'] = max_copiers

        return super().update(instance, validated_data)


class TrendingThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendingThreshold
        exclude = ('id',)
