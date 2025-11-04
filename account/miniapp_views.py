"""
Mini App Email Connection Views

Handles connecting email+password to Telegram-based accounts.
Supports both authenticated (Bearer token) and unauthenticated (init data) requests.
"""
import logging
import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, EmailOTPTelegramLink, AuthAuditLog
from .serializers import MiniAppConnectEmailSerializer, MiniAppVerifyOTPSerializer, UserSerializer
from .jwt_service import UnifiedJWTService

logger = logging.getLogger(__name__)


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that accepts token without 'Bearer ' prefix.
    Accepts both formats:
    - Authorization: Bearer <token>
    - Authorization: <token>
    """
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_raw_token(self, header):
        """
        Extract token from header, supporting both 'Bearer <token>' and '<token>' formats.
        """
        parts = header.split()

        if len(parts) == 0:
            return None

        # Support both "Bearer <token>" and "<token>" formats
        if len(parts) == 1:
            # Just the token without "Bearer"
            return parts[0]
        elif len(parts) == 2 and parts[0].lower() == 'bearer':
            # Traditional "Bearer <token>" format
            return parts[1]
        else:
            return None


class MiniAppConnectEmailThrottle(AnonRateThrottle):
    """Rate limit for OTP sending: 100 per hour per IP."""
    rate = '100/hour'


class MiniAppVerifyOTPThrottle(AnonRateThrottle):
    """Rate limit for OTP verification: 200 per hour per IP."""
    rate = '200/hour'


class MiniAppConnectEmailView(APIView):
    """
    Connect email+password to a Telegram-based account.
    Requires JWT token authentication (with or without 'Bearer ' prefix).
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = []  # Disabled for development
    
    @swagger_auto_schema(
        operation_description="""
        Connect email and password to your Telegram account. Sends a 6-digit OTP to the provided email.
        
        **Authentication:** Provide your JWT access token in the Authorization header.
        - Format: `Authorization: <your_token>` (without 'Bearer ' prefix)
        - Example: `Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
        """,
        request_body=MiniAppConnectEmailSerializer,
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "status": "otp_sent",
                        "email": "user@example.com",
                        "detail": "OTP sent to email"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request - validation error or email already taken",
                examples={
                    "application/json": {
                        "detail": "This email is already registered to another account"
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized - invalid or missing token",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT Access Token (without 'Bearer ' prefix)",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        tags=['Mini App Auth']
    )
    def post(self, request):
        # Validate request data
        serializer = MiniAppConnectEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Get user from authenticated request
        user = request.user
        telegram_id = user.telegram_id
        
        # Check that user has telegram_id
        if not telegram_id:
            return Response(
                {'detail': 'User must have a telegram_id to connect email'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email is already used by another account
        existing_user_with_email = User.objects.filter(email=email).exclude(telegram_id=telegram_id).first()
        if existing_user_with_email:
            return Response(
                {'detail': 'This email is already registered to another account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate OTP
        otp_code = self._generate_otp()
        otp_hash = self._hash_otp(otp_code)
        password_hash = make_password(password)
        
        # Store OTP with expiry (10 minutes)
        with transaction.atomic():
            # Invalidate any existing OTPs for this email+telegram combo
            EmailOTPTelegramLink.objects.filter(
                email=email,
                telegram_id=telegram_id,
                verified_at__isnull=True
            ).update(verified_at=timezone.now())  # Mark as used/invalid
            
            # Create new OTP record
            otp_record = EmailOTPTelegramLink.objects.create(
                user=user,
                email=email,
                code_hash=otp_hash,
                password=password_hash,
                telegram_id=telegram_id,
                expires_at=timezone.now() + timedelta(minutes=10),
                attempts=0
            )
        
        # Send OTP via email
        sent = self._send_otp_email(email, otp_code)
        
        if not sent:
            logger.error(f"Failed to send OTP to {email}")
            return Response(
                {'detail': 'Failed to send OTP. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Log the attempt
        self._log_audit(user, 'connect_email_otp_sent', email, success=True)
        
        logger.info(f"OTP sent to {email} for telegram_id {telegram_id}")
        
        return Response(
            {
                'status': 'otp_sent',
                'email': email,
                'detail': 'OTP sent to email'
            },
            status=status.HTTP_200_OK
        )
    
    def _generate_otp(self):
        """Generate 6-digit numeric OTP."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def _hash_otp(self, otp):
        """Hash OTP for secure storage."""
        return hashlib.sha256(otp.encode()).hexdigest()
    
    def _send_otp_email(self, email, otp_code):
        """Send OTP to user's email."""
        try:
            subject = 'Your Mazzaly Verification Code'
            message = f"""
Hello!

Your verification code is: {otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Mazzaly Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}", exc_info=True)
            return False
    
    def _log_audit(self, user, action, email, success=True, error_message=None):
        """Log authentication attempt."""
        ip_address = self._get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        AuthAuditLog.objects.create(
            user=user,
            action=action,
            platform='mini_app',
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message or ''
        )
    
    def _get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR')


class MiniAppVerifyOTPView(APIView):
    """
    Verify OTP and complete email+password linking.
    """
    permission_classes = [AllowAny]
    throttle_classes = []  # Disabled for development
    
    @swagger_auto_schema(
        operation_description="Verify the 6-digit OTP sent to your email and complete the email+password linking process. Returns JWT tokens upon success.",
        request_body=MiniAppVerifyOTPSerializer,
        responses={
            200: openapi.Response(
                description="OTP verified successfully, email linked",
                examples={
                    "application/json": {
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": 42,
                            "email": "user@example.com",
                            "telegram_id": "123456789",
                            "login_method": "both",
                            "is_email_verified": True
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid or expired OTP",
                examples={
                    "application/json": {
                        "detail": "Invalid OTP. 4 attempts remaining.",
                        "attempts_remaining": 4
                    }
                }
            ),
            404: openapi.Response(
                description="No pending verification found",
                examples={
                    "application/json": {
                        "detail": "No pending verification found for this email"
                    }
                }
            ),
            429: openapi.Response(
                description="Too many failed attempts",
                examples={
                    "application/json": {
                        "detail": "Too many failed attempts. Please request a new OTP."
                    }
                }
            ),
        },
        tags=['Mini App Auth']
    )
    def post(self, request):
        # Validate request data
        serializer = MiniAppVerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp_input = serializer.validated_data['otp']
        
        # Find the most recent valid OTP for this email
        otp_record = EmailOTPTelegramLink.objects.filter(
            email=email,
            verified_at__isnull=True
        ).order_by('-created_at').first()
        
        if not otp_record:
            return Response(
                {'detail': 'No pending verification found for this email'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if expired
        if otp_record.is_expired:
            return Response(
                {'detail': 'OTP has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check attempts limit
        if otp_record.attempts >= 5:
            return Response(
                {'detail': 'Too many failed attempts. Please request a new OTP.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Verify OTP
        otp_hash = hashlib.sha256(otp_input.encode()).hexdigest()
        
        if otp_hash != otp_record.code_hash:
            # Increment attempts
            otp_record.attempts += 1
            otp_record.save(update_fields=['attempts'])
            
            remaining = 5 - otp_record.attempts
            
            return Response(
                {
                    'detail': f'Invalid OTP. {remaining} attempts remaining.',
                    'attempts_remaining': remaining
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP is valid - complete the linking
        with transaction.atomic():
            user = otp_record.user
            
            if not user:
                # Shouldn't happen, but handle gracefully
                user = User.objects.get(telegram_id=otp_record.telegram_id)
            
            # Update user with email and password
            user.email = email
            user.set_password(otp_record.password)  # Password is already hashed, but set_password expects raw
            # Actually, the password is already hashed in otp_record.password
            # So we need to set it directly
            user.password = otp_record.password
            user.is_email_verified = True
            user.telegram_linked_at = timezone.now()
            
            # Update login method
            user.login_method = user.get_login_method()
            
            user.save(update_fields=['email', 'password', 'is_email_verified', 'telegram_linked_at', 'login_method'])
            
            # Mark OTP as verified
            otp_record.verified_at = timezone.now()
            otp_record.save(update_fields=['verified_at'])
            
            # Generate JWT tokens
            tokens = UnifiedJWTService.create_tokens(user)
            
            # Log successful verification
            self._log_audit(user, 'email_verified', email, success=True)
        
        logger.info(f"Email {email} verified and linked to user {user.id}")
        
        # Return tokens and user data
        response_data = UnifiedJWTService.create_unified_response(user, tokens)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _log_audit(self, user, action, email, success=True, error_message=None):
        """Log authentication attempt."""
        ip_address = self._get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        AuthAuditLog.objects.create(
            user=user,
            action=action,
            platform='mini_app',
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message or ''
        )
    
    def _get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR')
