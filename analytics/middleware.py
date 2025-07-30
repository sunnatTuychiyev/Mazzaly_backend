from .models import SiteVisit

class SiteVisitMiddleware:
    """Log a site visit once per user session."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ensure a session exists
        if not request.session.session_key:
            request.session.create()

        if not request.session.get('logged_visit'):
            ip = request.META.get('REMOTE_ADDR')
            SiteVisit.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                ip_address=ip,
            )
            request.session['logged_visit'] = True

        response = self.get_response(request)
        return response
