from django.utils import timezone
from .models import RecipeCardHourlyVisit, RecipeCardDailyVisit


def log_recipe_card_visit(request) -> None:
    """Record a unique visit to the recipe card API."""
    ip = request.META.get('REMOTE_ADDR')
    ua = request.META.get('HTTP_USER_AGENT', '')[:256]
    now = timezone.now()

    hour = now.replace(minute=0, second=0, microsecond=0)
    day = now.date()

    # Ensure only one record per IP/UA per period
    RecipeCardHourlyVisit.objects.get_or_create(
        ip_address=ip, user_agent=ua, hour=hour
    )
    RecipeCardDailyVisit.objects.get_or_create(
        ip_address=ip, user_agent=ua, day=day
    )
