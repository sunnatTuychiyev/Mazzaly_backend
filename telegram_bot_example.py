"""Minimal Telegram bot that sends a WebApp button on /start."""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import urlencode

import httpx
from decouple import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Config ---
WEBAPP_URL = config("WEBAPP_URL", default="https://localhost:8000/telegram/recipes/")
TOKEN = config("TELEGRAM_BOT_TOKEN", default=None)
AUTH_URL = config("TELEGRAM_AUTH_URL", default=None)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to /start with a greeting and a WebApp button."""
    user = update.effective_user

    if TOKEN and AUTH_URL and user:
        payload = {
            "user": json.dumps(
                {
                    "id": user.id,
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "username": user.username or "",
                }
            ),
            "auth_date": str(int(time.time())),
        }
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
        secret_key = hashlib.sha256(TOKEN.encode()).digest()
        payload["hash"] = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        init_data = urlencode(payload)
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(AUTH_URL, json={"init_data": init_data})
        except httpx.HTTPError as exc:
            logger.warning("Auto sign-up failed: %s", exc)

    button = InlineKeyboardButton(
        text="Retsept qo'shish", web_app=WebAppInfo(url=WEBAPP_URL)
    )
    await update.message.reply_text(
        "Assalomu alaykum! Mazzaly saytiga retsept qo'shmoqchi bo'lsangiz, "
        "ushbu tugmani bosing:",
        reply_markup=InlineKeyboardMarkup([[button]]),
    )


async def _run_bot_async() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def main() -> None:
    if not TOKEN:
        raise RuntimeError(
            "Set the TELEGRAM_BOT_TOKEN environment variable before running this script."
        )
    asyncio.run(_run_bot_async())


if __name__ == "__main__":
    main()
