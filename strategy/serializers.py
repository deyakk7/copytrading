from rest_framework import serializers

from crypto.models import Crypto, CryptoInUser
from crypto.serializers import CryptoSerializer
from strategy.models import Strategy, UsersInStrategy, UserOutStrategy
from strategy.utils import get_current_exchange_rate_usdt
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
    minutes = serializers.IntegerField(min_value=1)
    new_percentage_change_profit = serializers.DecimalField(max_digits=30, decimal_places=7)
    custom_avg_profit = serializers.DecimalField(max_digits=30, decimal_places=7, read_only=True)

    class Meta:
        model = Strategy
        fields = ['custom_avg_profit', 'new_percentage_change_profit', 'minutes']


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
    total_deposited = serializers.DecimalField(max_digits=30, decimal_places=7, read_only=True)
    users = StrategyUserSerializer(many=True, read_only=True)
    custom_avg_profit = serializers.DecimalField(max_digits=30, decimal_places=7, read_only=True)
    total_copiers = serializers.IntegerField(read_only=True)

    class Meta:
        model = Strategy
        fields = ['id', 'name', 'cryptos', 'trader', 'about', 'avg_profit', 'max_deposit', 'min_deposit',
                  'total_deposited', 'users', 'total_copiers', 'max_users', 'custom_avg_profit',
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
        exchange_rate = get_current_exchange_rate_usdt()
        for crypto_data in cryptos_data:
            Crypto.objects.create(strategy=strategy, exchange_rate=exchange_rate[crypto_data['name']], **crypto_data)
        return strategy

    def update(self, instance, validated_data):
        cryptos_data = validated_data.pop('crypto', None)
        instance.name = validated_data.get('name', instance.name)
        instance.about = validated_data.get('about', instance.about)
        instance.trader = validated_data.get('trader', instance.trader)
        instance.min_deposit = validated_data.get('min_deposit', instance.min_deposit)
        instance.max_deposit = validated_data.get('max_deposit', instance.max_deposit)
        instance.max_users = validated_data.get('max_users', instance.max_users)
        instance.custom_avg_profit = validated_data.get('custom_avg_profit', instance.custom_avg_profit)

        instance.save()

        if cryptos_data is None:
            return instance
        exchange_rate = get_current_exchange_rate_usdt()
        keep_cryptos = []
        for crypto_data in cryptos_data:
            crypto = instance.crypto.filter(name=crypto_data['name'], strategy=instance).first()
            if crypto:
                crypto.total_value = crypto_data.get('total_value', crypto.total_value)
                crypto.side = crypto_data.get('side', crypto.side)
                crypto.save()
                keep_cryptos.append(crypto.id)
                continue
            c = Crypto.objects.create(strategy=instance, exchange_rate=exchange_rate[crypto_data['name']],
                                      **crypto_data)
            keep_cryptos.append(c.id)

        for crypto in instance.crypto.all():
            if crypto.id not in keep_cryptos:
                crypto.delete()
        instance.save()

        crypto_in_strategy = [c.name for c in instance.crypto.all()]

        users = instance.users.all()

        for user_in_strategy in users:
            for crypto in user_in_strategy.crypto.all():
                print(crypto.name)
                if crypto.name not in crypto_in_strategy:
                    crypto.delete()
                    continue
            for crypto in crypto_in_strategy:
                if crypto not in [c.name for c in user_in_strategy.crypto.all()]:
                    CryptoInUser.objects.create(user_in_strategy=user_in_strategy, name=crypto,
                                                exchange_rate=exchange_rate[crypto])

        return instance
