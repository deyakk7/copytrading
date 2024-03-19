from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_of_registration', 'wallet', 'ip')
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
