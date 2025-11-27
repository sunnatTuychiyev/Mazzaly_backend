# Mazzaly_backend/middleware.py

class DisableSSLRedirectForSwagger:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/swagger"):
            request._dont_enforce_ssl_redirect = True
        return self.get_response(request)
