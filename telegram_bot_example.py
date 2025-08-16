"""Minimal Telegram bot that sends a WebApp button on /start."""

import asyncio

from decouple import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Read configuration from environment variables for convenience
WEBAPP_URL = config("WEBAPP_URL", default="https://localhost:8000/telegram/recipes/")
TOKEN = config("TELEGRAM_BOT_TOKEN", default=None)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to /start with a greeting and a WebApp button."""
    button = InlineKeyboardButton(
        text="Retsept qo'shish",
        web_app=WebAppInfo(url=WEBAPP_URL),
    )
    await update.message.reply_text(
        "Assalomu alaykum! Mazzaly saytiga retsept qo'shmoqchi bo'lsangiz, "
        "ushbu tugmani bosing:",
        reply_markup=InlineKeyboardMarkup([[button]]),
    )

def main() -> None:
    if TOKEN is None:
        raise RuntimeError(
            "Set the TELEGRAM_BOT_TOKEN environment variable before running this script."
        )

    async def run_bot() -> None:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))

        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await app.updater.idle()

    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
