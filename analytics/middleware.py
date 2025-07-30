from django.utils import timezone
from .models import SiteVisit

class SiteVisitMiddleware:
    """Log a site visit when /api/recipe-cards/ is requested."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only count visits when the main recipe API is called
        if request.path.startswith('/api/recipe-cards/'):
            if not request.session.session_key:
                request.session.create()

            today = timezone.localdate()
            if request.session.get('logged_visit') != str(today):
                ip = request.META.get('REMOTE_ADDR')
                SiteVisit.objects.get_or_create(
                    session_key=request.session.session_key,
                    date=today,
                    defaults={
                        'user': request.user if request.user.is_authenticated else None,
                        'ip_address': ip,
                    },
                )
                request.session['logged_visit'] = str(today)

        response = self.get_response(request)
        return response
