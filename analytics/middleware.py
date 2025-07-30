from django.utils.deprecation import MiddlewareMixin
from .models import VisitorStatistics

class VisitorTrackingMiddleware(MiddlewareMixin):
    """Record unique visitors for the recipe cards API."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/api/recipe-cards'):
            session_id = request.session.session_key
            if not session_id:
                # Ensure a session exists so we can uniquely track this visitor
                request.session.save()
                session_id = request.session.session_key

            ip_addr = (
                request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
                or request.META.get("REMOTE_ADDR", "")
            )

            if not VisitorStatistics.objects.filter(session_id=session_id).exists():
                VisitorStatistics.objects.create(
                    session_id=session_id,
                    ip_address=ip_addr,
                    user=request.user if request.user.is_authenticated else None,
                )
        return None
