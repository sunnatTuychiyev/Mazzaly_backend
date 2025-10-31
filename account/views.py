from rest_framework import generics, status, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from .models import User, EmailOTP, Author, TelegramLinkToken, EmailOTPTelegramLink, AuthAuditLog
from .serializers import (
    RegisterSerializer, UserSerializer, VerifyEmailSerializer, TelegramAuthSerializer, 
    AuthorSerializer, AdminUserCreateSerializer, TelegramLinkTokenResponseSerializer,
    TelegramLinkConfirmSerializer, EmailOTPSendSerializer, EmailOTPVerifySerializer
)
import random
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import SafeTokenRefreshSerializer
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import secrets
import logging
from .bot_auth import BotInternalAuthentication
try:  # pragma: no cover - drf_yasg optional
    from drf_yasg.utils import swagger_auto_schema
    from drf_yasg import openapi
except Exception:  # pragma: no cover - drf_yasg optional
    def swagger_auto_schema(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func
        return decorator

    class openapi:  # type: ignore
        class Schema:
            def __init__(self, *args, **kwargs):
                pass

        class Response:
            def __init__(self, *args, **kwargs):
                pass

        TYPE_OBJECT = TYPE_STRING = None
from social_django.utils import psa
from urllib.parse import parse_qsl
import json
import hashlib
import hmac
import time

# Import unified JWT service
from .jwt_service import UnifiedJWTService

def get_tokens_for_user(user):
    """Return refresh and access tokens for the given user (backward compatible)."""
    return UnifiedJWTService.create_tokens(user)


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
            # Log failed attempt
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            AuthAuditLog.objects.create(
                user=None,
                action='web_login',
                platform='web',
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message='Invalid credentials'
            )
            
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
        
        # Update last login and log audit
        user.last_login_at = timezone.now()
        user.login_method = user.get_login_method()  # Update login method
        user.save(update_fields=['last_login_at', 'login_method'])
        
        # Get client info
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Audit log
        AuthAuditLog.objects.create(
            user=user,
            action='web_login',
            platform='web',
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        # Return unified format (same as telegram login)
        return Response(
            UnifiedJWTService.create_unified_response(user, tokens),
            status=status.HTTP_200_OK
        )


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
        
        # Update login_method if needed
        user.login_method = user.get_login_method()
        user.save(update_fields=['login_method'])
        
        tokens = get_tokens_for_user(user)
        
        # Return unified format
        return UnifiedJWTService.create_unified_response(user, tokens)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Auth'],
        responses={200: UserSerializer},
        security=[{'Bearer': []}],
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all().order_by('name')
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AdminUserCreateSerializer
    permission_classes = [permissions.IsAdminUser]

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
    """
    Unified Telegram authentication endpoint.
    
    Returns IDENTICAL format as web login:
    {
        "access": "eyJhbGci...",
        "refresh": "eyJhbGci...",
        "user": {...}
    }
    """
    @swagger_auto_schema(
        tags=['Auth'],
        request_body=TelegramAuthSerializer,
        responses={
            200: openapi.Response('Authentication successful', UserSerializer),
            400: 'Invalid init data',
        },
    )
    def post(self, request):
        from .telegram_auth_service import TelegramAuthService
        
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        init_data = serializer.validated_data['init_data']
        
        try:
            # Verify Telegram authentication
            telegram_data = TelegramAuthService.verify_telegram_auth(init_data)
            
            if not telegram_data['telegram_id']:
                return Response(
                    {'detail': 'Invalid user data'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Login or create user (returns user, access_token, refresh_token)
            user, access_token, refresh_token = TelegramAuthService.telegram_login(
                telegram_data,
                request=request
            )
            
            # Return unified format (SAME as web login)
            return Response(
                UnifiedJWTService.create_unified_response(
                    user,
                    tokens={'access': access_token, 'refresh': refresh_token}
                ),
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            # Log failed attempt
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            AuthAuditLog.objects.create(
                user=None,
                action='telegram_login',
                platform='telegram',
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e)
            )
            
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in TelegramAuthView: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Authentication failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


logger = logging.getLogger(__name__)


class TelegramLinkTokenView(APIView):
    """Generate a one-time token for linking Telegram account to web user."""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Telegram Linking'],
        responses={
            200: openapi.Response('Token created', TelegramLinkTokenResponseSerializer),
            400: 'User already linked or rate limit exceeded',
        },
        security=[{'Bearer': []}],
    )
    def post(self, request):
        user = request.user
        
        # Check if user already has telegram_id
        if user.telegram_id:
            return Response(
                {'detail': 'Telegram account already linked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rate limiting: max 5 tokens per hour per user
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_tokens = TelegramLinkToken.objects.filter(
            user=user,
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_tokens >= 5:
            return Response(
                {'detail': 'Too many token requests. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(minutes=20)  # 20 minute expiry
        
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create token
        link_token = TelegramLinkToken.objects.create(
            token=token,
            user=user,
            expires_at=expires_at,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # Generate Telegram bot link
        # Bot username .env fayilidan bot_usern=@username formatida olinadi
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', None)
        if not bot_username:
            # .env dan olish
            from decouple import config
            bot_username_raw = config('bot_usern', default='').strip()
            # @ belgisini olib tashlash
            if bot_username_raw.startswith('@'):
                bot_username = bot_username_raw[1:]
            elif bot_username_raw:
                bot_username = bot_username_raw
            else:
                bot_username = 'YourBot'  # Default fallback
                logger.warning("bot_usern not set in .env, using default 'YourBot'")
        telegram_link = f"https://t.me/{bot_username}?start={token}"
        
        logger.info(
            f"Created Telegram link token for user {user.id} ({user.email}), "
            f"IP: {client_ip}"
        )
        
        return Response({
            'token': token,
            'link': telegram_link
        }, status=status.HTTP_200_OK)
    
    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TelegramLinkConfirmView(APIView):
    """Confirm token and link telegram_id to user account (called by bot)."""
    authentication_classes = [BotInternalAuthentication]
    permission_classes = [permissions.AllowAny]  # Bot auth is handled by authentication class
    
    @swagger_auto_schema(
        tags=['Telegram Linking'],
        request_body=TelegramLinkConfirmSerializer,
        responses={
            200: 'Telegram account linked successfully',
            400: 'Invalid token or telegram_id already in use',
            404: 'Token not found or expired',
        },
    )
    def post(self, request):
        serializer = TelegramLinkConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_str = serializer.validated_data['token']
        telegram_id = serializer.validated_data['telegram_id']
        username = serializer.validated_data.get('username', '')
        
        try:
            link_token = TelegramLinkToken.objects.get(token=token_str)
        except TelegramLinkToken.DoesNotExist:
            logger.warning(f"Invalid link token attempt: {token_str[:8]}...")
            return Response(
                {'detail': 'Invalid or expired token'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check token validity
        if not link_token.is_valid:
            if link_token.is_expired:
                return Response(
                    {'detail': 'Token has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if link_token.is_used:
                return Response(
                    {'detail': 'Token has already been used'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if telegram_id is already linked to another user
        existing_user = User.objects.filter(telegram_id=telegram_id).first()
        if existing_user and existing_user != link_token.user:
            logger.warning(
                f"Telegram ID {telegram_id} already linked to user {existing_user.id}"
            )
            return Response(
                {'detail': 'This Telegram account is already linked to another user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Link telegram_id to user
        with transaction.atomic():
            user = link_token.user
            user.telegram_id = telegram_id
            user.telegram_username = username if username else None
            user.telegram_linked_at = timezone.now()
            # Update login_method
            user.login_method = user.get_login_method()
            user.save(update_fields=['telegram_id', 'telegram_username', 'telegram_linked_at', 'login_method'])
            
            link_token.used_at = timezone.now()
            link_token.save(update_fields=['used_at'])
        
        # Audit log
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        AuthAuditLog.objects.create(
            user=user,
            action='link_telegram',
            platform='telegram',
            telegram_id=telegram_id,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        logger.info(
            f"Successfully linked Telegram ID {telegram_id} to user {user.id} "
            f"({user.email})"
        )
        
        return Response({
            'detail': 'Telegram account linked successfully',
            'user_id': user.id,
            'email': user.email,
        }, status=status.HTTP_200_OK)


class EmailOTPSendView(APIView):
    """Send OTP to email for linking email to Telegram account (Mini App flow)."""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        tags=['Email Verification'],
        request_body=EmailOTPSendSerializer,
        responses={
            200: 'OTP sent to email',
            400: 'Invalid request or rate limit exceeded',
        },
    )
    def post(self, request):
        serializer = EmailOTPSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        telegram_id = serializer.validated_data['telegram_id']
        
        # Rate limiting: max 3 OTP requests per email per hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_otps = EmailOTPTelegramLink.objects.filter(
            email=email,
            telegram_id=telegram_id,
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_otps >= 3:
            return Response(
                {'detail': 'Too many OTP requests. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Generate OTP code
        code = f"{random.randint(100000, 999999)}"
        expires_at = timezone.now() + timedelta(minutes=10)  # 10 minute expiry
        
        # Invalidate old valid OTP records for this email+telegram_id
        EmailOTPTelegramLink.objects.filter(
            email=email,
            telegram_id=telegram_id,
            verified_at__isnull=True,
            expires_at__gt=timezone.now(),
            attempts__lt=5
        ).update(verified_at=timezone.now())  # Invalidate old ones
        
        otp_record = EmailOTPTelegramLink.objects.create(
            email=email,
            code=code,
            telegram_id=telegram_id,
            expires_at=expires_at
        )
        
        # Send email
        try:
            send_mail(
                'Email Verification for Telegram Account',
                f'Your verification code is {code}. This code will expire in 10 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
            logger.info(f"Sent OTP to {email} for Telegram ID {telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            otp_record.delete()
            return Response(
                {'detail': 'Failed to send verification email'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'detail': 'Verification code sent to email'
        }, status=status.HTTP_200_OK)


class EmailOTPVerifyView(APIView):
    """Verify OTP and link email to Telegram account (extends existing verify-email endpoint)."""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        tags=['Email Verification'],
        request_body=EmailOTPVerifySerializer,
        responses={
            200: openapi.Response('Email verified and linked', UserSerializer),
            400: 'Invalid code or expired',
        },
    )
    def post(self, request):
        serializer = EmailOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        telegram_id = serializer.validated_data['telegram_id']
        
        otp_record = EmailOTPTelegramLink.objects.filter(
            email=email,
            telegram_id=telegram_id,
            code=code
        ).order_by('-created_at').first()
        
        if not otp_record:
            return Response(
                {'detail': 'Invalid email or code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Increment attempts
        otp_record.attempts += 1
        otp_record.save(update_fields=['attempts'])
        
        # Check validity
        if not otp_record.is_valid:
            if otp_record.is_expired:
                return Response(
                    {'detail': 'Verification code has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if otp_record.is_verified:
                return Response(
                    {'detail': 'Verification code has already been used'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if otp_record.attempts >= 5:
                return Response(
                    {'detail': 'Too many failed attempts'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Verify code
        if otp_record.code != code:
            return Response(
                {'detail': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Link email to Telegram account
        with transaction.atomic():
            # Check if user with this email exists
            try:
                user = User.objects.get(email=email)
                # If user already has telegram_id and it's different, reject
                if user.telegram_id and user.telegram_id != telegram_id:
                    return Response(
                        {'detail': 'This email is already linked to a different Telegram account'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Link telegram_id to existing user
                user.telegram_id = telegram_id
                user.telegram_linked_at = timezone.now()
                user.is_email_verified = True
                user.login_method = user.get_login_method()
                user.save(update_fields=['telegram_id', 'telegram_linked_at', 'is_email_verified', 'login_method'])
            except User.DoesNotExist:
                # Check if telegram_id user exists
                telegram_user = User.objects.filter(telegram_id=telegram_id).first()
                if telegram_user:
                    # Update existing telegram user with email
                    telegram_user.email = email
                    telegram_user.is_email_verified = True
                    telegram_user.telegram_linked_at = timezone.now()
                    telegram_user.login_method = telegram_user.get_login_method()
                    telegram_user.save(update_fields=['email', 'is_email_verified', 'telegram_linked_at', 'login_method'])
                    user = telegram_user
                else:
                    # Create new user
                    # Extract name from email or use defaults
                    name_parts = email.split('@')[0].split('.')
                    first_name = name_parts[0].capitalize() if name_parts else 'User'
                    last_name = name_parts[1].capitalize() if len(name_parts) > 1 else ''
                    
                    user = User.objects.create_user(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        telegram_id=telegram_id,
                        is_email_verified=True,
                        login_method=User.LOGIN_METHOD_BOTH,
                        created_via=User.CREATED_VIA_TELEGRAM,
                        telegram_linked_at=timezone.now()
                    )
            
            # Mark OTP as verified
            otp_record.verified_at = timezone.now()
            otp_record.save(update_fields=['verified_at'])
        
        # Update login_method
        user.login_method = user.get_login_method()
        user.save(update_fields=['login_method'])
        
        # Generate tokens
        tokens = get_tokens_for_user(user)
        
        # Audit log
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        AuthAuditLog.objects.create(
            user=user,
            action='link_email',
            platform='telegram',
            telegram_id=telegram_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        logger.info(
            f"Successfully linked email {email} to Telegram ID {telegram_id}, user ID: {user.id}"
        )
        
        # Return unified format
        return Response(
            UnifiedJWTService.create_unified_response(user, tokens),
            status=status.HTTP_200_OK
        )
