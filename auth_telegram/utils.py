import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl

from django.conf import settings


class TelegramInitDataError(Exception):
    """Raised when Telegram init data is invalid."""


def verify_init_data(init_data: str) -> dict:
    """Validate Telegram init data according to Telegram Mini App docs.

    Returns the parsed parameters (without the hash) on success.
    """
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_value = params.pop('hash', None)
    if not hash_value:
        raise TelegramInitDataError('Missing hash')

    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b'WebAppData', settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc_hash, hash_value):
        raise TelegramInitDataError('Invalid hash')

    auth_date = int(params.get('auth_date', '0'))
    if time.time() - auth_date > 86400:
        raise TelegramInitDataError('Auth date expired')

    return params
