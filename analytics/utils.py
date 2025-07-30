from .models import SiteVisit


def log_site_visit(request):
    """Record a unique visit based on the session key."""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    if not SiteVisit.objects.filter(session_key=session_key).exists():
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        SiteVisit.objects.create(
            session_key=session_key,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip,
        )
