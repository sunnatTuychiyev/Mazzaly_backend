from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from .models import User, EmailOTP
from .serializers import RegisterSerializer, UserSerializer, VerifyEmailSerializer
import random
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from social_django.utils import psa

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
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
        token = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'token': str(token.access_token)
        }, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    @swagger_auto_schema(
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
        token = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'token': str(token.access_token)
        }, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={200: UserSerializer},
        security=[{'Bearer': []}],
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

class GoogleAuthView(APIView):
    @swagger_auto_schema(
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
