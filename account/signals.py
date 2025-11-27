from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User, Subscription


@receiver(post_save, sender=User)
def create_default_subscription(sender, instance, created, **kwargs):
    if not created:
        return

    from django.conf import settings

    if getattr(settings, 'PROMO_PREMIUM_ON_SIGNUP', False):
        premium_subscription = Subscription.objects.create(
            user=instance,
            plan=Subscription.PLAN_PREMIUM,
            start_date=timezone.now(),
        )

        premium_end_date = premium_subscription.end_date or premium_subscription.start_date

        Subscription.objects.create(
            user=instance,
            plan=Subscription.PLAN_STANDARD,
            start_date=premium_end_date,
        )
    else:
        Subscription.objects.create(user=instance, plan=Subscription.PLAN_STANDARD)
