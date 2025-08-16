import os
import sys
from threading import Thread

from django.apps import AppConfig

class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'

    def ready(self):
        import account.signals  # noqa
        if os.environ.get("RUN_MAIN") == "true" and "runserver" in sys.argv:
            if os.getenv("TELEGRAM_BOT_TOKEN"):
                from telegram_bot_example import main as run_bot
                Thread(target=run_bot, daemon=True).start()
