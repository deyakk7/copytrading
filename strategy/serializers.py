from django.db import transaction as trans
from django.db.models import Sum
from rest_framework import serializers

from crypto.models import Crypto
from crypto.serializers import CryptoSerializer
from strategy.models import Strategy, UsersInStrategy, UserOutStrategy
from trader.models import Trader


class StrategyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersInStrategy
        fields = ['user', 'value', 'profit', 'strategy', 'date_of_adding', 'custom_profit', 'current_custom_profit']

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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['profits'] = instance.profits.all().order_by('-date').values_list('value', flat=True)
        return data

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
        with trans.atomic():
            if usdt_value != 0:
                Crypto.objects.create(strategy=strategy, name='USDT', total_value=usdt_value, side=None)
            for crypto_data in cryptos_data:
                Crypto.objects.create(strategy=strategy, **crypto_data)
        return strategy

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
                    raise serializers.ValidationError({'error': 'Total copiers must be less than max copiers in trader'})

                with trans.atomic():
                    instance.trader.copiers_count = \
                        Strategy.objects.filter(trader=instance.trader).aggregate(
                            total_copiers_sum=Sum('total_copiers'))[
                            'total_copiers_sum'] - instance.total_copiers + validated_data.get('total_copiers')
                    instance.trader.save()
                    instance.total_copiers = validated_data.get('total_copiers', instance.total_copiers)

        instance.save()

        if cryptos_data is None:
            return instance
        keep_cryptos = []

        sum_of_percent = 0
        with trans.atomic():
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

        return instance
