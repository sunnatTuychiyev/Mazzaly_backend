from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btn = InlineKeyboardButton(text="Mazzaly Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
    await update.message.reply_text(
        "Mini appni ochish uchun bosin:",
        reply_markup=InlineKeyboardMarkup([[btn]])
    )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()


if __name__ == "__main__":
    main()
