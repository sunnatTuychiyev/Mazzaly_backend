from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# URL of the mini app hosted by this Django project
WEBAPP_URL = "https://<your-domain>/telegram/recipes/"

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
    application = Application.builder().token("<TELEGRAM_BOT_TOKEN>").build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()
