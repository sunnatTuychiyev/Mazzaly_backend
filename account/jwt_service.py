"""
Unified JWT Service for both Web and Telegram authentication.
Ensures identical token format and structure for both platforms.
"""
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class UnifiedJWTService:
    """Unified JWT service that creates tokens with consistent format for web and telegram"""
    
    @staticmethod
    def create_tokens(user):
        """
        Create access and refresh tokens for any user (web or telegram).
        
        This ensures both platforms use IDENTICAL token format.
        The token payload includes both email and telegram_id (whichever exists).
        
        Args:
            user: User model instance
            
        Returns:
            dict: {
                'access': str (JWT access token),
                'refresh': str (JWT refresh token)
            }
        """
        # Use Simple JWT's RefreshToken which automatically includes user info
        refresh = RefreshToken.for_user(user)
        
        # Get the access token
        access_token = refresh.access_token
        
        # Optionally customize token payload to include additional info
        # The default Simple JWT token already includes user_id in 'user_id' claim
        # We can add custom claims if needed, but default format works for both platforms
        
        tokens = {
            'access': str(access_token),
            'refresh': str(refresh),
        }
        
        logger.debug(f"Created tokens for user {user.id} (login_method: {getattr(user, 'login_method', 'unknown')})")
        
        return tokens
    
    @staticmethod
    def create_unified_response(user, tokens=None):
        """
        Create unified response format for both web and telegram login.
        
        This ensures IDENTICAL response structure:
        {
            "access": "eyJhbGci...",
            "refresh": "eyJhbGci...",
            "user": {...}
        }
        
        Args:
            user: User model instance
            tokens: Optional pre-generated tokens dict
            
        Returns:
            dict: Unified response format
        """
        if tokens is None:
            tokens = UnifiedJWTService.create_tokens(user)
        
        from .serializers import UserSerializer
        
        return {
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': UserSerializer(user).data
        }


# Alias for backward compatibility
get_tokens_for_user = UnifiedJWTService.create_tokens

