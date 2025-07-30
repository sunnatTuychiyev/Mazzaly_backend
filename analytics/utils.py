from django.utils import timezone
from .models import HourlyVisit, DailyVisit


def record_unique_visit(request):
    """Record a unique visit for the /api/recipe-cards/ endpoint."""
    ip = request.META.get('REMOTE_ADDR') or ''
    # Handle X-Forwarded-For if behind a proxy
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    now = timezone.now()
    hour = now.replace(minute=0, second=0, microsecond=0)
    day = now.date()

    if ip:
        HourlyVisit.objects.get_or_create(
            ip_address=ip, user_agent=user_agent, hour=hour
        )
        DailyVisit.objects.get_or_create(
            ip_address=ip, user_agent=user_agent, day=day
        )
