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


class HourlyVisit(models.Model):
    """Unique visit to recipe cards within a specific hour."""

    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    hour = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ip_address', 'user_agent', 'hour')
        ordering = ['hour']


class DailyVisit(models.Model):
    """Unique visit to recipe cards within a specific day."""

    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    day = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ip_address', 'user_agent', 'day')
        ordering = ['day']
