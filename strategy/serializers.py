import decimal

from django.db import transaction as trans
from django.db.models import Sum
from rest_framework import serializers

from crypto.models import Crypto
from crypto.serializers import CryptoSerializer, NewCryptoForStrategy
from strategy.models import Strategy, UsersInStrategy, UserOutStrategy
from strategy.utils import get_current_exchange_rate_usdt, update_all_cryptos, recalculate_percentage_in_strategy
from trader.models import Trader
from transaction.models import TransactionOpen
from transaction.utils import create_open_transaction, create_close_transaction, averaging_open_transaction


class StrategyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersInStrategy
        exclude = ['saved_profit', 'custom_profit', 'current_custom_profit', 'id', 'different_profit_from_strategy']

    def validate(self, data):
        super().validate(data)

        strategy = Strategy.objects.get(id=data['strategy'].id)
        if strategy.users.filter(user_id=data['user']):
            raise serializers.ValidationError({'error': "User already exists in strategy"})

        if data['value'] > strategy.max_deposit:
            raise serializers.ValidationError({"error": "Value must be less than max deposit"})

        if data['value'] < strategy.min_deposit:
            raise serializers.ValidationError({"error": "Value must be greater than min deposit"})

        return data


class StrategyDepositingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    trader_deposit = serializers.DecimalField(max_digits=30, decimal_places=2, required=False)

    class Meta:
        model = Strategy
        fields = ['id', 'trader_deposit']


class UserCopingStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersInStrategy
        fields = ['value']


class StrategyCustomProfitSerializer(serializers.ModelSerializer):
    new_percentage_change_profit = serializers.DecimalField(max_digits=30, decimal_places=7)
    custom_avg_profit = serializers.DecimalField(max_digits=30, decimal_places=7, read_only=True)

    class Meta:
        model = Strategy
        fields = ['custom_avg_profit', 'new_percentage_change_profit']


class UserOutStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOutStrategy
        fields = '__all__'


class UserInStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersInStrategy
        fields = '__all__'


class StrategyUserListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    trader = serializers.CharField(source='strategy.trader.nickname')
    strategy = serializers.CharField(source='strategy.name')

    class Meta:
        model = UsersInStrategy
        fields = ['username', 'trader', 'strategy', 'value', 'date_of_adding']


class StrategySerializer(serializers.ModelSerializer):
    cryptos = CryptoSerializer(many=True, source='crypto')
    trader = serializers.PrimaryKeyRelatedField(queryset=Trader.objects.all(), required=False)
    avg_profit = serializers.DecimalField(max_digits=30, decimal_places=2, read_only=True)
    total_deposited = serializers.DecimalField(max_digits=30, decimal_places=2, read_only=True)
    users = StrategyUserSerializer(many=True, read_only=True)
    custom_avg_profit = serializers.DecimalField(max_digits=30, decimal_places=7, read_only=True)
    total_copiers = serializers.IntegerField(required=False)
    trader_deposit = serializers.DecimalField(max_digits=30, decimal_places=2, required=False)

    class Meta:
        model = Strategy
        fields = ['id', 'name', 'cryptos', 'trader', 'about', 'avg_profit', 'max_deposit', 'min_deposit',
                  'total_deposited', 'users', 'total_copiers', 'custom_avg_profit',
                  'current_custom_profit', 'trader_deposit', 'available_pool']

    def __init__(self, *args, **kwargs):
        super(StrategySerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.method in ['PUT', 'PATCH']:
            self.fields['new_cryptos'] = NewCryptoForStrategy(many=True, required=False)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['profits'] = instance.profits.all().order_by('date').values_list('value', flat=True)
        return data

    @trans.atomic()
    def create(self, validated_data):
        cryptos_data = validated_data.pop('crypto', None)
        strategy = Strategy.objects.create(**validated_data)

        if cryptos_data is None:
            return strategy

        update_all_cryptos(strategy=strategy, crypto_data=cryptos_data)

        return strategy

    @trans.atomic()
    def update(self, instance: Strategy, validated_data):
        cryptos_data = validated_data.pop('crypto', None)
        instance.name = validated_data.get('name', instance.name)
        instance.about = validated_data.get('about', instance.about)
        instance.trader = validated_data.get('trader', instance.trader)
        instance.min_deposit = validated_data.get('min_deposit', instance.min_deposit)
        instance.max_deposit = validated_data.get('max_deposit', instance.max_deposit)
        instance.custom_avg_profit = validated_data.get('custom_avg_profit', instance.custom_avg_profit)
        instance.trader_deposit = validated_data.get('trader_deposit', instance.trader_deposit)

        if instance.trader:
            current_available_copiers = instance.trader.max_copiers - instance.trader.copiers_count

            if validated_data.get('total_copiers') is not None:
                if validated_data.get('total_copiers') - instance.total_copiers > current_available_copiers:
                    raise serializers.ValidationError(
                        {'error': 'Total copiers must be less than max copiers in trader'})

                instance.trader.copiers_count = \
                    Strategy.objects.filter(trader=instance.trader).aggregate(
                        total_copiers_sum=Sum('total_copiers'))[
                        'total_copiers_sum'] - instance.total_copiers + validated_data.get('total_copiers')

                instance.trader.save()
                instance.total_copiers = validated_data.get('total_copiers', instance.total_copiers)

        instance.save()

        crypto_pool_input = validated_data.get('new_cryptos', None)

        if cryptos_data is None and crypto_pool_input is None:
            return instance

        crypto_percentage_in_pool = {x['name']: {
            'total_value': decimal.Decimal(x['total_value']),
            'side': x['side']
        } for x in crypto_pool_input if x['name'] != 'USDT'}

        sum_in_modal = 0

        for name, item in crypto_percentage_in_pool.items():
            sum_in_modal += item['total_value']

        if sum_in_modal > 100:
            raise serializers.ValidationError({'error': 'Percentage cannot be more than 100'})

        """ 
        if trader is not setup we have to change only crypto to new value without any transaction logic 
        """
        if instance.trader is None:
            update_all_cryptos(strategy=instance, crypto_data=cryptos_data)
            return instance

        exchange_rate = get_current_exchange_rate_usdt()

        cryptos_db = Crypto.objects.filter(
            strategy=instance
        )
        crypto_names = {x['name']: decimal.Decimal(x['total_value']) for x in cryptos_data if x['name'] != 'USDT'}

        '''Step 1. Looks for deleted and decreases crypto'''
        for crypto_db in cryptos_db:
            if crypto_db.name == 'USDT':
                continue

            current_crypto_value = crypto_names.get(crypto_db.name, 0)

            if current_crypto_value > 100:
                trans.set_rollback(True)
                raise serializers.ValidationError({'error': 'Percentage cannot be more than 100'})

            '''If admin delete the crypto'''
            if current_crypto_value == 0:
                open_transaction = TransactionOpen.objects.filter(
                    strategy=instance,
                    crypto_pair=crypto_db.name + "USDT"
                ).first()

                create_close_transaction(open_transaction, exchange_rate, current_crypto_value)
                crypto_db.delete()
                open_transaction.delete()

            elif current_crypto_value == 100:
                continue

            else:
                open_transaction = TransactionOpen.objects.filter(
                    strategy=instance,
                    crypto_pair=crypto_db.name + "USDT"
                ).first()

                create_close_transaction(open_transaction, exchange_rate, current_crypto_value)

                crypto_db.total_value = current_crypto_value * open_transaction.percentage

                open_transaction.save()
                crypto_db.save()

        instance.refresh_from_db()
        recalculate_percentage_in_strategy(strategy=instance, exchange_rate=exchange_rate)
        instance.refresh_from_db()

        crypto_pool = {x['name']: {
            'total_value': decimal.Decimal(
                (x['total_value'] * instance.available_pool / 100) * 100 / instance.trader_deposit),
            'side': x['side']
        } for x in crypto_pool_input if x['name'] != 'USDT'}

        '''Step 2. Look for new crypto and add more percentage to current from pool'''
        pool_money_decrease = 0
        if instance.available_pool != 0:
            for name, value in crypto_pool.items():
                crypto_db: Crypto = Crypto.objects.filter(
                    strategy=instance,
                    name=name
                ).first()

                '''if there no opened transaction with this crypto name'''
                if crypto_db is None:
                    crypto_db_new = Crypto.objects.create(
                        name=name,
                        strategy=instance,
                        total_value=value['total_value'],
                        side=value['side'],
                    )

                    _, pool_money_trans = create_open_transaction(
                        crypto_db_new,
                        exchange_rate,
                        crypto_percentage_in_pool[crypto_db_new.name]['total_value'],
                    )
                    pool_money_decrease += pool_money_trans

                elif crypto_db.side != value['side']:
                    open_transaction: TransactionOpen = TransactionOpen.objects.filter(
                        strategy=instance,
                        crypto_pair=name + "USDT"
                    ).first()

                    create_close_transaction(open_transaction, exchange_rate, open_transaction.percentage)
                    open_transaction.delete()

                    crypto_db.side = value['side']
                    crypto_db.total_value = value['total_value']

                    crypto_db.save()

                    _, pool_money_trans = create_open_transaction(
                        crypto_data=crypto_db,
                        exchange_rate=exchange_rate,
                        percentage_from_pool=crypto_percentage_in_pool[crypto_db.name]['total_value']
                    )
                    pool_money_decrease += pool_money_trans

                else:
                    crypto_db.total_value += value['total_value']
                    print(value['total_value'])
                    print(crypto_db.total_value)
                    crypto_db.save()

                    open_transaction = TransactionOpen.objects.filter(
                        strategy=instance,
                        crypto_pair=name + "USDT",
                    ).first()

                    pool_money = averaging_open_transaction(
                        crypto_db,
                        open_transaction,
                        exchange_rate,
                        crypto_percentage_in_pool[crypto_db.name]['total_value']
                    )

                    pool_money_decrease += pool_money

            instance.available_pool -= pool_money_decrease

        if instance.available_pool == 0:
            usdt_crypto = Crypto.objects.filter(
                strategy=instance,
                name='USDT'
            ).first()

            if usdt_crypto is not None:
                usdt_crypto.delete()

        else:
            Crypto.objects.update_or_create(
                strategy=instance,
                name='USDT',
                defaults={
                    'total_value': (instance.available_pool / instance.trader_deposit) * 100,
                    'side': None
                }
            )

        instance.save()

        return instance
