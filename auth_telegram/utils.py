import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl


class TelegramInitDataError(Exception):
    """Raised when Telegram init data is invalid."""


def verify_init_data(init_data: str, bot_token: str, max_age: int = 86400) -> dict:
    """Validate Telegram init data according to Telegram Mini App docs.

    ``bot_token`` is the Telegram bot token used to derive the secret key.
    ``max_age`` specifies the maximum allowed age (in seconds) for ``auth_date``.
    Returns a dictionary containing the parsed key/value pairs (without the
    ``hash``) and a decoded ``user`` object if present.
    """
    if not bot_token:
        raise TelegramInitDataError('Bot token not provided')
    
    if not init_data:
        raise TelegramInitDataError('Init data is empty')
    
    # Parse init_data - parse_qsl automatically handles URL decoding
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_value = params.pop('hash', None)
    
    if not hash_value:
        raise TelegramInitDataError('Missing hash')

    # Create data check string: sort alphabetically, join with newline
    # This must match exactly what Telegram expects
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(params.items()))
    
    # Calculate secret key: HMAC-SHA256('WebAppData', bot_token)
    secret_key = hmac.new(
        b'WebAppData',
        bot_token.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Calculate hash: HMAC-SHA256(secret_key, data_check_string)
    calc_hash = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Verify hash using constant-time comparison
    if not hmac.compare_digest(calc_hash, hash_value):
        raise TelegramInitDataError('Invalid hash')

    # Check auth_date expiration
    auth_date = int(params.get('auth_date', '0'))
    if time.time() - auth_date > max_age:
        raise TelegramInitDataError('Auth date expired')

    # Parse user data
    user_json = params.get('user')
    user = json.loads(user_json) if user_json else None
    return {"data": params, "user": user}
