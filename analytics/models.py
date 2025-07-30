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


class SiteVisit(models.Model):
    """Tracks unique visits to the site."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='site_visits'
    )
    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.session_key} @ {self.timestamp}"
