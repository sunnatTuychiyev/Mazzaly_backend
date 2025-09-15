from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
from .models import User, EmailOTP, Author
import re

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

    def validate_password(self, value):
        if (
            len(value) < 8 or
            not re.search(r'[A-Z]', value) or
            not re.search(r'[a-z]', value) or
            not re.search(r'\d', value)
        ):
            raise serializers.ValidationError(
                'Password must be at least 8 characters, contain uppercase, lowercase, and digit.'
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), allow_null=True, required=False)
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'telegram_id', 'author')


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name', 'bio')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Do not include empty bio in API output
        if not data.get('bio'):
            data.pop('bio', None)
        return data


class AdminUserCreateSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), allow_null=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'telegram_id', 'password', 'author')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class TelegramAuthSerializer(serializers.Serializer):
    init_data = serializers.CharField()


class SafeTokenRefreshSerializer(TokenRefreshSerializer):
    """Return a clear error instead of 500 when the user for the token no longer exists."""

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except get_user_model().DoesNotExist:
            raise InvalidToken('User not found')

