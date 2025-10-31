"""Authentication utilities for bot→backend communication."""
from rest_framework import authentication, exceptions
from django.conf import settings


class BotInternalAuthentication(authentication.BaseAuthentication):
    """Authenticate bot requests using BOT_INTERNAL_SECRET."""
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ', 1)[1]
        expected_secret = settings.BOT_INTERNAL_SECRET
        
        if not expected_secret:
            raise exceptions.AuthenticationFailed('BOT_INTERNAL_SECRET not configured')
        
        if token != expected_secret:
            return None
        
        # Return a tuple (user, auth) where user is None for internal bot auth
        # We use a special user-like object to identify bot requests
        return (None, {'is_bot': True})
    
    def authenticate_header(self, request):
        return 'Bearer'

