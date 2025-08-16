"""Minimal Telegram bot that sends a WebApp button on /start."""

from decouple import config
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
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
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()
