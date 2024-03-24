from rest_framework import serializers

from transaction.models import Transaction, Transfer, UserDeposit


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('id',)


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
