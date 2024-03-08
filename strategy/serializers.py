from rest_framework import serializers

from crypto.models import Crypto
from crypto.serializers import CryptoSerializer
from strategy.models import Strategy


class StrategySerializer(serializers.ModelSerializer):
    cryptos = CryptoSerializer(many=True, source='crypto')
    trader = serializers.PrimaryKeyRelatedField(read_only=True, required=False)

    class Meta:
        model = Strategy
        fields = ['id', 'name', 'cryptos', 'trader']

    def create(self, validated_data):
        if "trader" not in validated_data.keys():
            raise serializers.ValidationError("Trader is required")

        cryptos_data = validated_data.pop('crypto')
        strategy = Strategy.objects.create(**validated_data)
        for crypto_data in cryptos_data:
            Crypto.objects.create(strategy=strategy, **crypto_data)
        return strategy

    def update(self, instance, validated_data):
        cryptos_data = validated_data.pop('crypto')
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        keep_cryptos = []
        for crypto_data in cryptos_data:
            c = Crypto.objects.create(strategy=instance, **crypto_data)
            keep_cryptos.append(c.id)

        for crypto in instance.crypto.all():
            if crypto.id not in keep_cryptos:
                crypto.delete()

        return instance
