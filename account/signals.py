from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Subscription

@receiver(post_save, sender=User)
def create_default_subscription(sender, instance, created, **kwargs):
    if created:
        Subscription.objects.create(user=instance, plan=Subscription.PLAN_STANDARD)
