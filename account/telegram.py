import json

from django.conf import settings

from .models import User
from auth_telegram.utils import verify_init_data, TelegramInitDataError


def get_user_from_init_data(init_data: str) -> User:
    """Validate Telegram init data and return the associated user.

    The init data string is validated according to Telegram's guidelines. If the
    user does not yet exist it will be created automatically using their
    Telegram ID.
    """
    res = verify_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
    user_data = res.get("user") or {}
    telegram_id = str(user_data.get("id")) if user_data else None
    if not telegram_id:
        raise TelegramInitDataError("Invalid user data")

    user, _ = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "email": f"tg_{telegram_id}@example.com",
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "is_email_verified": True,
        },
    )
    return user
