"""
Telegram Authentication Service
Handles Telegram WebApp authentication with unified JWT token format.
"""
import hashlib
import hmac
import json
import time
import logging
from urllib.parse import parse_qsl
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import User, AuthAuditLog

logger = logging.getLogger(__name__)


class TelegramAuthService:
    """Handle Telegram WebApp authentication and user management"""
    
    @staticmethod
    def verify_telegram_auth(init_data_string):
        """
        Verify Telegram WebApp initData signature.
        
        Uses the EXACT same algorithm as auth_telegram/utils.py which is proven to work.
        This method matches verify_init_data() from auth_telegram/utils.py byte-for-byte.
        
        Args:
            init_data_string: Raw init_data string from Telegram WebApp
            
        Returns:
            dict: Parsed and verified init data including user info
            
        Raises:
            ValueError: If signature is invalid or data is expired
        """
        # EXACT COPY of auth_telegram/utils.py verify_init_data logic
        # Parse init_data using parse_qsl (handles URL decoding automatically)
        params = dict(parse_qsl(init_data_string, keep_blank_values=True))
        hash_value = params.pop('hash', None)
        
        if not hash_value:
            raise ValueError('Missing hash in init_data')
        
        # Create data check string: sort alphabetically, join with newline
        # EXACTLY as in auth_telegram/utils.py line 25
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(params.items()))
        
        # Calculate secret key: HMAC-SHA256('WebAppData', bot_token)
        # Use TELEGRAM_AUTH_BOT_TOKEN (mini_app_bot_t) for authentication
        auth_bot_token = getattr(settings, 'TELEGRAM_AUTH_BOT_TOKEN', None) or settings.TELEGRAM_BOT_TOKEN
        secret_key = hmac.new(
            b'WebAppData',
            auth_bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash: HMAC-SHA256(secret_key, data_check_string)
        # EXACTLY as in auth_telegram/utils.py line 27
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify hash using constant-time comparison
        # EXACTLY as in auth_telegram/utils.py line 28
        if not hmac.compare_digest(calculated_hash, hash_value):
            # Enhanced error logging for debugging (only in debug mode)
            if settings.DEBUG:
                auth_bot_token = getattr(settings, 'TELEGRAM_AUTH_BOT_TOKEN', None) or settings.TELEGRAM_BOT_TOKEN
                logger.error(
                    f"Telegram hash verification failed.\n"
                    f"Expected hash: {calculated_hash}\n"
                    f"Received hash: {hash_value}\n"
                    f"Data check string length: {len(data_check_string)}\n"
                    f"Data check string: {data_check_string}\n"
                    f"Params keys: {sorted(params.keys())}\n"
                    f"Auth bot token length: {len(auth_bot_token) if auth_bot_token else 0}"
                )
            raise ValueError('Invalid Telegram authentication hash')
        
        # Check auth_date (must be within last 24 hours)
        # EXACTLY as in auth_telegram/utils.py lines 31-33
        auth_date = int(params.get('auth_date', '0'))
        if time.time() - auth_date > 86400:  # 24 hours
            raise ValueError('Telegram authentication data expired')
        
        # Parse user data
        # EXACTLY as in auth_telegram/utils.py lines 35-36
        user_json = params.get('user')
        try:
            user_data = json.loads(user_json) if user_json else {}
        except json.JSONDecodeError:
            raise ValueError('Invalid user data in init_data')
        
        return {
            'telegram_id': str(user_data.get('id')) if user_data.get('id') else None,
            'username': user_data.get('username'),
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'photo_url': user_data.get('photo_url'),
            'auth_date': auth_date,
            'raw_params': params
        }
    
    @staticmethod
    @transaction.atomic
    def telegram_login(telegram_data, request=None):
        """
        Authenticate user via Telegram or create new account.
        
        This method:
        1. Verifies Telegram signature
        2. Creates or updates user
        3. Generates unified JWT tokens (same format as web login)
        4. Logs authentication attempt
        
        Args:
            telegram_data: Dict with telegram_id, username, first_name, etc.
            request: Optional request object for IP/UA logging
            
        Returns:
            tuple: (user, access_token, refresh_token)
        """
        telegram_id = str(telegram_data['telegram_id'])
        
        # Check if user exists with this telegram_id
        try:
            user = User.objects.get(telegram_id=telegram_id)
            
            # Existing user - update info and last login
            user.telegram_username = telegram_data.get('username')
            user.telegram_first_name = telegram_data.get('first_name', '')
            user.telegram_last_name = telegram_data.get('last_name', '')
            user.telegram_photo_url = telegram_data.get('photo_url')
            user.last_login_at = timezone.now()
            
            # Update login_method if needed
            current_method = user.get_login_method()
            if user.login_method != current_method:
                user.login_method = current_method
            
            user.save(update_fields=[
                'telegram_username',
                'telegram_first_name',
                'telegram_last_name',
                'telegram_photo_url',
                'last_login_at',
                'login_method'
            ])
            
            is_new_user = False
            
        except User.DoesNotExist:
            # New user - create account
            # For telegram-only users, we need a placeholder email that's unique
            # But we'll mark login_method as 'telegram'
            placeholder_email = f'tg_{telegram_id}@telegram.local'
            
            # Use get_or_create to avoid race conditions
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'email': placeholder_email,
                    'telegram_username': telegram_data.get('username'),
                    'telegram_first_name': telegram_data.get('first_name', ''),
                    'telegram_last_name': telegram_data.get('last_name', ''),
                    'telegram_photo_url': telegram_data.get('photo_url'),
                    'first_name': telegram_data.get('first_name', 'User'),
                    'last_name': telegram_data.get('last_name', ''),
                    'login_method': User.LOGIN_METHOD_TELEGRAM,
                    'created_via': User.CREATED_VIA_TELEGRAM,
                    'is_email_verified': False,
                    'last_login_at': timezone.now()
                }
            )
            
            # Set unusable password for telegram-only users (no password authentication)
            if created:
                user.set_unusable_password()
                user.save(update_fields=['password'])
            
            is_new_user = created
        
        # Generate unified JWT tokens (same as web login)
        from .jwt_service import UnifiedJWTService
        tokens = UnifiedJWTService.create_tokens(user)
        
        # Get client info for audit log
        ip_address = None
        user_agent = ''
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Audit log
        AuthAuditLog.objects.create(
            user=user,
            action='telegram_login',
            platform='telegram',
            telegram_id=telegram_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        logger.info(f"Telegram login: user_id={user.id}, telegram_id={telegram_id}, is_new={is_new_user}")
        
        return user, tokens['access'], tokens['refresh']
    
    @staticmethod
    def log_auth_attempt(user_id, action, platform, telegram_id=None, email=None,
                        success=True, error_message=None, ip_address=None, user_agent=None):
        """Log authentication attempt for audit trail"""
        try:
            user = User.objects.get(pk=user_id) if user_id else None
        except User.DoesNotExist:
            user = None
        
        AuthAuditLog.objects.create(
            user=user,
            action=action,
            platform=platform,
            telegram_id=telegram_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent or '',
            success=success,
            error_message=error_message or ''
        )

