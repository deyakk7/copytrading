from rest_framework import serializers

from crypto.models import Crypto


class CryptoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crypto
        exclude = ('strategy', 'id')
        read_only_fields = ('id', 'strategy')
