from django.utils import timezone

from .models import RecipeCardVisit


def log_recipe_card_visit(request) -> None:
    """Record a unique visit to the recipe card list endpoint."""
    ip = request.META.get("REMOTE_ADDR")
    agent = request.META.get("HTTP_USER_AGENT", "")
    hour_ago = timezone.now() - timezone.timedelta(hours=1)
    if not RecipeCardVisit.objects.filter(
        ip_address=ip,
        user_agent=agent,
        timestamp__gte=hour_ago,
    ).exists():
        RecipeCardVisit.objects.create(ip_address=ip, user_agent=agent)
