from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from account.models import User, AuthAuditLog
from account.jwt_service import UnifiedJWTService
from account.telegram_auth_service import TelegramAuthService
from .utils import verify_init_data, TelegramInitDataError


class MiniAppIndexView(TemplateView):
    template_name = 'miniapp/index.html'


class AuthorPickerView(TemplateView):
    template_name = 'miniapp/author_picker.html'


class TestInitDataView(TemplateView):
    """Init data ni test qilish uchun sahifa"""
    template_name = 'miniapp/test_init_data.html'


@method_decorator(csrf_exempt, name='dispatch')
class TelegramLoginView(APIView):
    """
    Unified Telegram Mini App login endpoint.
    
    Returns IDENTICAL format as web login:
    {
        "access": "eyJhbGci...",
        "refresh": "eyJhbGci...",
        "user": {...}
    }
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        init_data = request.data.get('init_data', '')
        
        try:
            # Use unified Telegram auth service
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
            
            # Create unified response
            response_data = UnifiedJWTService.create_unified_response(
                user,
                tokens={'access': access_token, 'refresh': refresh_token}
            )
            
            # Create response with cookie (for Mini App compatibility)
            response = Response(response_data, status=status.HTTP_200_OK)
            response.set_cookie(
                'access', access_token, httponly=True, secure=True,
                samesite='None', path='/', max_age=3600
            )
            
            return response
            
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
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in TelegramLoginView: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Authentication failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'telegram_id': user.telegram_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
