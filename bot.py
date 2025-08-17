import os
from dotenv import load_dotenv, find_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv(find_dotenv(), override=True)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not TOKEN or TOKEN.startswith("<"):
    raise RuntimeError("TELEGRAM_BOT_TOKEN env var is missing or invalid")
if not WEBAPP_URL or WEBAPP_URL.startswith("https://<"):
    raise RuntimeError("WEBAPP_URL env var is missing or invalid")


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
