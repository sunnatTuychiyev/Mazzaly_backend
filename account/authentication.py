from rest_framework_simplejwt.authentication import JWTAuthentication

class FlexibleJWTAuthentication(JWTAuthentication):
    """Allow Authorization header without the 'Bearer' prefix."""

    def get_header(self, request):
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return None
        if not header.lower().startswith('bearer '):
            header = 'Bearer ' + header
        return header.encode('iso-8859-1')

