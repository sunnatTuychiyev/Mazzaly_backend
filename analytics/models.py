from django.db import models
from django.conf import settings
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


class RecipeCardHourlyVisit(models.Model):
    """Unique visit to the recipe card API within a specific hour."""

    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=256)
    hour = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ip_address', 'user_agent', 'hour')
        ordering = ['-hour']

    def __str__(self) -> str:
        return f"{self.ip_address} - {self.user_agent} @ {self.hour}"


class RecipeCardDailyVisit(models.Model):
    """Unique visit to the recipe card API within a specific day."""

    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=256)
    day = models.DateField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ip_address', 'user_agent', 'day')
        ordering = ['-day']

    def __str__(self) -> str:
        return f"{self.ip_address} - {self.user_agent} on {self.day}"
