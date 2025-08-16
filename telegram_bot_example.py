"""Minimal Telegram bot that sends a WebApp button on /start."""

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Read configuration from environment variables for convenience
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://localhost:8000/telegram/recipes/")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if TOKEN is None:
    raise RuntimeError("Set the TELEGRAM_BOT_TOKEN environment variable before running this script.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a WebApp button that opens the recipe submission form."""
    button = InlineKeyboardButton(
        text="🍳 Yangi retsept",
        web_app=WebAppInfo(url=WEBAPP_URL),
    )
    await update.message.reply_text(
        "Retsept yuborish uchun tugmani bosing:",
        reply_markup=InlineKeyboardMarkup([[button]]),
    )

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()
