from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import requests

from .models import UserRecipe


def _get_frontend_url(recipe_id: int) -> str:
    origin = getattr(settings, "FRONTEND_ORIGIN", settings.BACKEND_ORIGIN)
    origin = origin.rstrip("/")
    return f"{origin}/my/recipes/{recipe_id}"


@receiver(pre_save, sender=UserRecipe)
def store_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._previous_status = old.status
        except sender.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=UserRecipe)
def notify_status_change(sender, instance, created, **kwargs):
    prev_status = getattr(instance, "_previous_status", None)
    if created or prev_status == instance.status or not instance.telegram_user_id:
        return
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return
    if instance.status == UserRecipe.STATUS_APPROVED:
        url = _get_frontend_url(instance.id)
        text = (
            f"✅ Retseptingiz qabul qilindi! Saytga kirib tekshirishingiz mumkin: {url}"
        )
    elif instance.status == UserRecipe.STATUS_REJECTED:
        text = (
            "❌ Afsus, retseptingiz rad etildi. Iltimos, talablarni ko'rib chiqing va qayta yuboring."
        )
    else:
        return
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": instance.telegram_user_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(api_url, json=payload, timeout=5)
    except requests.RequestException:
        pass
