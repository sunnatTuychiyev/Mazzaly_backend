import json
import time
import hmac
import hashlib
from urllib.parse import parse_qsl

from django.conf import settings

from .models import User

class TelegramInitDataError(Exception):
    """Raised when Telegram init data is invalid."""


def get_user_from_init_data(init_data: str) -> User:
    """Validate Telegram init data and return the associated user.

    The init data string is validated according to Telegram's guidelines. If the
    user does not yet exist it will be created automatically using their
    Telegram ID.
    """
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_value = params.pop('hash', None)
    if not hash_value:
        raise TelegramInitDataError('Missing hash')

    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(
        b"WebAppData",
        settings.TELEGRAM_BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if calc_hash != hash_value:
        raise TelegramInitDataError('Invalid hash')

    auth_date = int(params.get('auth_date', '0'))
    if time.time() - auth_date > 86400:
        raise TelegramInitDataError('Auth date expired')

    user_data = json.loads(params.get('user', '{}'))
    telegram_id = str(user_data.get('id')) if user_data else None
    if not telegram_id:
        raise TelegramInitDataError('Invalid user data')

    user, _ = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'email': f'tg_{telegram_id}@example.com',
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'is_email_verified': True,
        },
    )
    return user
