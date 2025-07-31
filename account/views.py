from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from .models import User, EmailOTP
from .serializers import RegisterSerializer, UserSerializer, VerifyEmailSerializer, TelegramAuthSerializer
import random
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import SafeTokenRefreshSerializer
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from social_django.utils import psa
from urllib.parse import parse_qsl
import json
import hashlib
import hmac
import time

def get_tokens_for_user(user):
    """Return refresh and access tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT token obtain endpoint with Swagger tag."""

    @swagger_auto_schema(tags=['Auth'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    """JWT token refresh endpoint with Swagger tag."""
    serializer_class = SafeTokenRefreshSerializer

    @swagger_auto_schema(tags=['Auth'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        tags=['Auth'],
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('User created', UserSerializer),
            400: 'Invalid input',
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        code = f"{random.randint(100000, 999999)}"
        EmailOTP.objects.update_or_create(user=user, defaults={'code': code})
        send_mail(
            'Email Verification',
            f'Your verification code is {code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return Response({'detail': 'Verification code sent to email.'}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    @swagger_auto_schema(
        tags=['Auth'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
            },
            required=['email', 'password'],
        ),
        responses={
            200: openapi.Response('Login successful', UserSerializer),
            400: 'Invalid credentials',
        },
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_email_verified:
            code = f"{random.randint(100000, 999999)}"
            EmailOTP.objects.update_or_create(user=user, defaults={'code': code})
            send_mail(
                'Email Verification',
                f'Your verification code is {code}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            return Response({'detail': 'Email not verified. Verification code sent.'}, status=status.HTTP_400_BAD_REQUEST)
        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        }, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    @swagger_auto_schema(
        tags=['Auth'],
        request_body=VerifyEmailSerializer,
        responses={200: 'Email verified', 400: 'Invalid code'},
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        try:
            user = User.objects.get(email=email)
            otp = user.email_otp
        except (User.DoesNotExist, EmailOTP.DoesNotExist):
            return Response({'detail': 'Invalid email or code'}, status=status.HTTP_400_BAD_REQUEST)
        if otp.code != code:
            return Response({'detail': 'Invalid email or code'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_email_verified = True
        user.save()
        otp.delete()
        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        }, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Auth'],
        responses={200: UserSerializer},
        security=[{'Bearer': []}],
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

class GoogleAuthView(APIView):
    @swagger_auto_schema(
        tags=['Auth'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Google access token'),
            },
            required=['access_token'],
        ),
        responses={
            200: openapi.Response('Authentication successful', UserSerializer),
            400: 'Invalid token or authentication error',
        },
    )
    @psa('social:complete')
    def post(self, request, *args, **kwargs):
        token = request.data.get('access_token')
        if not token:
            return Response({'error': 'No access token provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Authenticate using the access token
            user = request.backend.do_auth(token)
            if user and user.is_active:
                jwt_token = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'token': str(jwt_token.access_token)
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Google authentication failed or user is inactive'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Authentication error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class TelegramAuthView(APIView):
    @swagger_auto_schema(
        tags=['Auth'],
        request_body=TelegramAuthSerializer,
        responses={
            200: openapi.Response('Authentication successful', UserSerializer),
            400: 'Invalid init data',
        },
    )
    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        init_data = serializer.validated_data['init_data']
        params = dict(parse_qsl(init_data, keep_blank_values=True))
        hash_value = params.pop('hash', None)
        if not hash_value:
            return Response({'error': 'Missing hash'}, status=status.HTTP_400_BAD_REQUEST)
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(params.items()))
        secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
        calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calc_hash != hash_value:
            return Response({'error': 'Invalid hash'}, status=status.HTTP_400_BAD_REQUEST)
        auth_date = int(params.get('auth_date', '0'))
        if time.time() - auth_date > 86400:
            return Response({'error': 'Auth date expired'}, status=status.HTTP_400_BAD_REQUEST)
        user_data = json.loads(params.get('user', '{}'))
        telegram_id = str(user_data.get('id')) if user_data else None
        if not telegram_id:
            return Response({'error': 'Invalid user data'}, status=status.HTTP_400_BAD_REQUEST)
        user, _ = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'email': f'tg_{telegram_id}@example.com',
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'is_email_verified': True,
            },
        )
        token = RefreshToken.for_user(user)
        return Response({'user': UserSerializer(user).data, 'token': str(token.access_token)})
