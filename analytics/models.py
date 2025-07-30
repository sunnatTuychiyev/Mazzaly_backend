from django.db import models
from django.conf import settings
from django.utils import timezone
from recipes.models import Recipe


class RecipeViewLog(models.Model):
    """Stores each time a recipe detail is viewed."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipe_views'
    )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='view_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.recipe} viewed by {self.user} on {self.timestamp}"


class RecipeCardVisit(models.Model):
    """Unique visits to the recipe cards API."""

    PERIOD_HOUR = "hour"
    PERIOD_DAY = "day"

    PERIOD_CHOICES = [
        (PERIOD_HOUR, "Hour"),
        (PERIOD_DAY, "Day"),
    ]

    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=256)
    period_start = models.DateTimeField()
    period_type = models.CharField(max_length=4, choices=PERIOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("ip_address", "user_agent", "period_start", "period_type")

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.ip_address} {self.period_type} @ {self.period_start}"


def record_recipe_card_visit(request) -> None:
    """Log a visit to the recipe cards API respecting uniqueness constraints."""

    ip = request.META.get("REMOTE_ADDR", "")
    ua = request.META.get("HTTP_USER_AGENT", "")[:255]
    now = timezone.now()
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    RecipeCardVisit.objects.get_or_create(
        ip_address=ip,
        user_agent=ua,
        period_start=hour_start,
        period_type=RecipeCardVisit.PERIOD_HOUR,
    )

    RecipeCardVisit.objects.get_or_create(
        ip_address=ip,
        user_agent=ua,
        period_start=day_start,
        period_type=RecipeCardVisit.PERIOD_DAY,
    )
