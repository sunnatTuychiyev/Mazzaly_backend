import os, re, sys
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
WEBAPP_URL = (os.getenv("WEBAPP_URL") or "").strip()

def valid_token(t):
    return bool(re.fullmatch(r"\d{6,12}:[A-Za-z0-9_-]{30,}", t))

if not valid_token(TOKEN):
    sys.exit("TELEGRAM_BOT_TOKEN missing/invalid. Set TELEGRAM_BOT_TOKEN in your environment or .env file.")
if not WEBAPP_URL.startswith("https://"):
    sys.exit("WEBAPP_URL must be public HTTPS.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btn = InlineKeyboardButton("Open Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
    await update.message.reply_text("Mini App:", reply_markup=InlineKeyboardMarkup([[btn]]))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
