#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading
from decouple import config


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Mazzaly_backend.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    run_main = os.environ.get("RUN_MAIN")
    werkzeug_run_main = os.environ.get("WERKZEUG_RUN_MAIN")
    if (
        any(cmd in sys.argv for cmd in ("runserver", "runserver_plus"))
        and config("TELEGRAM_BOT_TOKEN", default=None)
        and (
            run_main == "true"
            or werkzeug_run_main == "true"
            or "--noreload" in sys.argv
        )
    ):
        from telegram_bot_example import main as telegram_bot_main

        threading.Thread(target=telegram_bot_main, daemon=True).start()

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
