from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import serializers

from transaction.serializers import UserDepositSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    deposits = UserDepositSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'nickname', 'date_of_registration', 'wallet', 'deposits')
        extra_kwargs = {
            'date_of_registration': {'read_only': True},
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password',)

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
