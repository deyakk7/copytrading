from rest_framework import serializers

from crypto.models import Crypto
from crypto.serializers import CryptoSerializer
from strategy.models import Strategy, UsersInStrategy
from trader.models import Trader


class StrategyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersInStrategy
        fields = ['user', 'value', 'strategy', 'date_of_adding']

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
    avg_profit = serializers.DecimalField(max_digits=30, decimal_places=7, read_only=True)
    total_deposited = serializers.DecimalField(max_digits=30, decimal_places=7, required=False)
    users = StrategyUserSerializer(many=True, read_only=True)

    class Meta:
        model = Strategy
        fields = ['id', 'name', 'cryptos', 'trader', 'about', 'avg_profit', 'max_deposit', 'min_deposit',
                  'total_deposited', 'users', 'total_copiers']

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     if data['custom_profit'] is None:
    #         del data['custom_profit']
    #     return data

    def create(self, validated_data):
        # if "trader" not in validated_data.keys():
        #     raise serializers.ValidationError("Trader is required")

        cryptos_data = validated_data.pop('crypto', None)
        strategy = Strategy.objects.create(**validated_data)

        if cryptos_data is None:
            return strategy

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
        if validated_data.get('total_copiers') and instance.trader is not None:
            instance.trader.copiers_count -= instance.total_copiers
            instance.total_copiers = validated_data.get('total_copiers', instance.total_copiers)
            instance.trader.copiers_count += instance.total_copiers
            instance.trader.save()

        instance.save()

        if cryptos_data is None:
            return instance
        keep_cryptos = []
        for crypto_data in cryptos_data:
            c = Crypto.objects.create(strategy=instance, **crypto_data)
            keep_cryptos.append(c.id)

        for crypto in instance.crypto.all():
            if crypto.id not in keep_cryptos:
                crypto.delete()

        return instance
