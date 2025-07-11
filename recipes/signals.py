from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Recipe
from .translation_utils import translate_recipe

@receiver(post_save, sender=Recipe)
def auto_translate_recipe(sender, instance, created, **kwargs):
    translate_recipe(instance)
