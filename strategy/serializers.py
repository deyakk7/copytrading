from django.db import transaction as trans
from django.db.models import Sum
from rest_framework import serializers

from crypto.models import Crypto
from crypto.serializers import CryptoSerializer
from strategy.models import Strategy, UsersInStrategy, UserOutStrategy
from strategy.utils import get_current_exchange_rate_usdt
from trader.models import Trader
from transaction.models import TransactionOpen
from transaction.serializers import TransactionOpenListSerializer
from transaction.utils import create_open_transaction, create_close_transaction


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

    class Meta:
        model = Strategy
        fields = ['id', 'name', 'cryptos', 'trader', 'about', 'avg_profit', 'max_deposit', 'min_deposit',
                  'total_deposited', 'users', 'total_copiers', 'custom_avg_profit',
                  'current_custom_profit']

    def __init__(self, *args, **kwargs):
        super(StrategySerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.method in ['PUT', 'PATCH']:
            self.fields['open_transaction_list'] = TransactionOpenListSerializer(many=True, required=False)

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

        sum_of_percent = 0
        for crypto_data in cryptos_data:
            if crypto_data['name'] == 'USDT':
                continue
            sum_of_percent += crypto_data['total_value']

        if sum_of_percent > 100:
            raise serializers.ValidationError({'error': 'Sum of percent must be less or equal than 100'})

        usdt_value = 100 - sum_of_percent
        exchange_rate = get_current_exchange_rate_usdt()

        if usdt_value != 0:
            Crypto.objects.create(strategy=strategy, name='USDT', total_value=usdt_value, side=None)
        for crypto_data in cryptos_data:
            obj = Crypto.objects.create(strategy=strategy, **crypto_data)

            data = {
                "name": obj.name,
                "total_value": obj.total_value,
                "strategy": strategy.id,
                "side": obj.side,
            }

            create_open_transaction(data, exchange_rate)

        return strategy

    @trans.atomic()
    def update(self, instance, validated_data):
        cryptos_data = validated_data.pop('crypto', None)
        instance.name = validated_data.get('name', instance.name)
        instance.about = validated_data.get('about', instance.about)
        instance.trader = validated_data.get('trader', instance.trader)
        instance.min_deposit = validated_data.get('min_deposit', instance.min_deposit)
        instance.max_deposit = validated_data.get('max_deposit', instance.max_deposit)
        instance.custom_avg_profit = validated_data.get('custom_avg_profit', instance.custom_avg_profit)

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

        open_transaction_to_change = {}
        open_transaction_list = validated_data.get("open_transaction_list", None)

        if open_transaction_list:
            for item in open_transaction_list:
                open_transaction_to_change[item['transaction_id']] = item['value_change']

        if cryptos_data is None:
            return instance

        keep_cryptos = []

        crypto_before_change = (Crypto.objects.filter(strategy=instance).
                                values('strategy', 'name', 'total_value', 'side'))

        for crypto in crypto_before_change:
            print(crypto)

        sum_of_percent = 0

        for crypto_data in cryptos_data:
            if crypto_data['name'] == 'USDT':
                continue

            crypto = instance.crypto.filter(name=crypto_data['name'], strategy=instance).first()

            if crypto:
                crypto.total_value = crypto_data.get('total_value', crypto.total_value)
                crypto.side = crypto_data.get('side', crypto.side)

                crypto.save()

                sum_of_percent += crypto.total_value
                keep_cryptos.append(crypto.id)
                continue

            c = Crypto.objects.create(strategy=instance, **crypto_data)

            sum_of_percent += c.total_value
            keep_cryptos.append(c.id)

        usdt_crypto = instance.crypto.filter(name='USDT', strategy=instance).first()

        if sum_of_percent > 100:
            trans.set_rollback(True)
            raise serializers.ValidationError({'error': 'Sum of percent must be less or equal than 100'})

        needed_percentage = 100 - sum_of_percent

        if needed_percentage == 0 and usdt_crypto:
            usdt_crypto.delete()

        elif needed_percentage and usdt_crypto:
            usdt_crypto.total_value = needed_percentage
            usdt_crypto.save()
            keep_cryptos.append(usdt_crypto.id)

        else:
            c = Crypto.objects.create(strategy=instance, name="USDT", total_value=needed_percentage, side=None)
            keep_cryptos.append(c.id)

        for crypto in instance.crypto.all():
            if crypto.id not in keep_cryptos:
                crypto.delete()
        instance.save()

        exchange_rate = get_current_exchange_rate_usdt()

        used_crypto = set()
        used_crypto.add("USDT")

        for crypto_bf in crypto_before_change:
            if crypto_bf['name'] == 'USDT':
                continue

            crypto_db: Crypto = Crypto.objects.filter(
                name=crypto_bf['name'],
                strategy=instance,
            ).first()

            opened_transactions = TransactionOpen.objects.filter(
                strategy=instance,
                crypto_pair=crypto_bf['name'] + "USDT",
            )

            if crypto_db is None:
                for transaction in opened_transactions:
                    create_close_transaction(transaction, exchange_rate)

                    transaction.delete()

            elif crypto_bf['total_value'] < crypto_db.total_value and crypto_bf['side'] == crypto_db.side:
                crypto_bf['total_value'] = crypto_db.total_value - crypto_bf['total_value']

                create_open_transaction(crypto_bf, exchange_rate)

            elif crypto_bf['total_value'] > crypto_db.total_value and crypto_bf['side'] == crypto_db.side:
                for transaction_op in opened_transactions:
                    transaction_data_ = open_transaction_to_change.get(transaction_op.id, None)

                    if transaction_data_ is not None:
                        transaction_op.total_value -= transaction_data_

                        if transaction_op.total_value:
                            transaction_op.save()

                        transaction_op.total_value = transaction_data_
                        create_close_transaction(transaction_op, exchange_rate)

                        if transaction_op.total_value == 0:
                            transaction_op.delete()

                    else:
                        transaction_op.total_value = (crypto_bf['total_value'] - crypto_db.total_value)

                        create_close_transaction(transaction_op, exchange_rate)

                        transaction_op.total_value = crypto_db.total_value
                        transaction_op.save()

            elif crypto_bf['side'] != crypto_db.side:
                for transaction_op in opened_transactions:
                    create_close_transaction(transaction_op, exchange_rate)
                    transaction_op.delete()

                crypto_bf['side'] = crypto_db.side
                crypto_bf['total_value'] = crypto_db.total_value
                create_open_transaction(crypto_bf, exchange_rate)

            used_crypto.add(crypto_bf['name'])

        new_crypto_db = Crypto.objects.filter(
            strategy=instance,
        ).exclude(
            name__in=used_crypto
        ).values('strategy', 'name', 'total_value', 'side')

        for crypto in new_crypto_db:
            create_open_transaction(crypto, exchange_rate)

        return instance
