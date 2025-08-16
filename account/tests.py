import json
import hmac
import hashlib
import time
from urllib.parse import urlencode

from django.test import TestCase, override_settings

from .telegram import get_user_from_init_data, TelegramInitDataError
from .models import User


class TelegramInitDataTests(TestCase):
    @override_settings(TELEGRAM_BOT_TOKEN="testtoken")
    def test_user_created_from_valid_init_data(self):
        user_data = {"id": 1, "first_name": "Bob"}
        payload = {
            "auth_date": str(int(time.time())),
            "query_id": "AA123",
            "user": json.dumps(user_data, separators=(",", ":")),
        }
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
        secret_key = hmac.new(
            b"WebAppData", b"testtoken", hashlib.sha256
        ).digest()
        hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        init_data = urlencode({**payload, "hash": hash_value})

        user = get_user_from_init_data(init_data)
        self.assertIsInstance(user, User)
        self.assertEqual(user.telegram_id, "1")

    @override_settings(TELEGRAM_BOT_TOKEN="testtoken")
    def test_invalid_hash_raises_error(self):
        payload = {
            "auth_date": str(int(time.time())),
            "query_id": "AA123",
            "user": json.dumps({"id": 1}, separators=(",", ":")),
            "hash": "0" * 64,
        }
        init_data = urlencode(payload)
        with self.assertRaises(TelegramInitDataError):
            get_user_from_init_data(init_data)
