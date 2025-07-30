from django.utils import timezone

from .models import SiteVisit


def log_site_visit(request):
    """Record a unique visit for the current session and hour."""
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    now = timezone.now()
    start = now.replace(minute=0, second=0, microsecond=0)
    end = start + timezone.timedelta(hours=1)

    if not SiteVisit.objects.filter(session_key=session_key, timestamp__gte=start, timestamp__lt=end).exists():
        SiteVisit.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key,
            ip_address=request.META.get('REMOTE_ADDR')
        )
