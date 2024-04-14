from rest_framework import serializers

from transaction.models import TransactionClose, Transfer, UserDeposit


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionClose
        exclude = ('id', 'strategy')
        read_only_fields = ('id', 'strategy')


class TransactionOpenListSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    value_change = serializers.DecimalField(max_digits=30, decimal_places=7)


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = '__all__'
        read_only_fields = ('id',)


class UserDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeposit
        fields = '__all__'
        read_only_fields = ('id',)
