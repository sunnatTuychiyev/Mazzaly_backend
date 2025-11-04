import os
import re
import sys
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# .env fayilini yuklash
load_dotenv()

# Bot token va sozlamalar .env fayilidan olinadi
TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
BOT_USERNAME = (os.getenv("TELEGRAM_BOT_USERNAME") or "Mazzalybot").strip()
WEBAPP_URL = (os.getenv("WEBAPP_URL") or "").strip()
BACKEND_ORIGIN = (os.getenv("BACKEND_ORIGIN") or "").strip()
BOT_INTERNAL_SECRET = (os.getenv("BOT_INTERNAL_SECRET") or "").strip()

def valid_token(t):
    """Telegram bot token formatini tekshirish"""
    if not t:
        return False
    return bool(re.fullmatch(r"\d{6,12}:[A-Za-z0-9_-]{30,}", t))

def validate_config():
    """Sozlamalarni tekshirish va xatoliklarni ko'rsatish"""
    errors = []
    warnings = []
    
    # Token tekshiruvi
    if not TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN missing. .env fayiliga TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN qo'shing.")
    elif not valid_token(TOKEN):
        errors.append("TELEGRAM_BOT_TOKEN invalid format. Token formati: 123456:ABC-DEF...")
    
    # WEBAPP_URL tekshiruvi
    if not WEBAPP_URL:
        warnings.append("WEBAPP_URL not set. Mini App button won't work.")
    elif not WEBAPP_URL.startswith("https://"):
        warnings.append("WEBAPP_URL must start with https://")
    
    # Xatoliklarni ko'rsatish
    if errors:
        for error in errors:
            logger.error(f"ERROR: {error}")
        sys.exit(f"ERROR: {errors[0]}")
    
    # Ogohlantirishlarni ko'rsatish
    if warnings:
        for warning in warnings:
            logger.warning(f"WARNING: {warning}")
    
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start buyrug'i bajarilganda Mini App oynasini ochish yoki token tekshirish"""
    try:
        # Update va message tekshiruvi
        if not update or not update.message:
            logger.error("Invalid update object received")
            return
        
        # Token parametrini tekshirish (account linking uchun)
        args = context.args
        if args and len(args) > 0:
            token = args[0]
            # Bu token account linking token ekanligini tekshirish va backend ga yuborish
            await handle_link_token(update, token)
            return
        
        # Agar token bo'lmasa, odatdagi Mini App oynasini ochish
        # WEBAPP_URL tekshiruvi
        if not WEBAPP_URL or not WEBAPP_URL.startswith("https://"):
            error_msg = (
                "❌ Mini App URL sozlanmagan.\n\n"
                "WEBAPP_URL ni .env fayiliga qo'shing:\n"
                "WEBAPP_URL=https://your-domain.com/telegram/recipes/"
            )
            await update.message.reply_text(error_msg)
            logger.warning(f"User {update.effective_user.id} tried to start bot but WEBAPP_URL not configured")
            return
        
        # Mini App tugmasi yaratish
        btn = InlineKeyboardButton(
            "🚀 Mini App ni ochish", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
        
        keyboard = InlineKeyboardMarkup([[btn]])
        
        # Xush kelib sozlash
        welcome_text = (
            "👋 Xush kelibsiz!\n\n"
            "Mini App ni ochish uchun quyidagi tugmani bosing:"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard
        )
        
        # Log qilish
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username or user.first_name}) started the bot")
        
    except TelegramError as e:
        logger.error(f"Telegram error in start handler: {str(e)}")
        if update and update.message:
            try:
                await update.message.reply_text(
                    "❌ Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."
                )
            except:
                pass
    except Exception as e:
        logger.error(f"Unexpected error in start handler: {str(e)}", exc_info=True)
        if update and update.message:
            try:
                await update.message.reply_text(
                    "❌ Kutilmagan xatolik. Iltimos, keyinroq qayta urinib ko'ring."
                )
            except:
                pass

async def handle_link_token(update: Update, token: str):
    """
    Token tekshirish va backend webhook ga yuborish.
    Bu funksiya webhook endpoint'ini chaqiradi (yangi tizim).
    """
    import httpx
    
    user = update.effective_user
    telegram_id = str(user.id) if user else None
    username = user.username if user else ''
    first_name = user.first_name if user else ''
    last_name = user.last_name if user else ''
    
    if not telegram_id:
        await update.message.reply_text("❌ Telegram user ID topilmadi.")
        return
    
    if not BACKEND_ORIGIN:
        await update.message.reply_text(
            "❌ Server sozlamalari to'liq emas. Iltimos, administrator bilan bog'laning."
        )
        logger.error("BACKEND_ORIGIN sozlanmagan")
        return
    
    try:
        # Backend webhook endpoint'iga Telegram update formatida yuborish
        # Bu yangi /api/mini-app/auth/telegram-webhook/ endpoint'i
        webhook_payload = {
            "update_id": update.update_id,
            "message": {
                "message_id": update.message.message_id,
                "from": {
                    "id": int(telegram_id),
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username
                },
                "text": f"/start {token}"
            }
        }
        
        webhook_url = f"{BACKEND_ORIGIN}/api/mini-app/auth/telegram-webhook/"
        logger.info(f"Calling webhook: {webhook_url}")
        logger.info(f"Payload: {webhook_payload}")
        
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.post(
                webhook_url,
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            logger.info(f"Webhook response status: {response.status_code}")
            logger.info(f"Webhook response body: {response.text}")
            
            if response.status_code == 200:
                # Webhook o'zi user'ga xabar yuboradi, bot duplicate xabar yubormasin
                logger.info(f"Successfully linked Telegram ID {telegram_id} using token {token[:8]}...")
            else:
                # Agar webhook xatolik qaytarsa
                await update.message.reply_text(
                    "❌ Link yaroqsiz yoki muddati o'tgan. Iltimos, web saytdan yangi link oling."
                )
                logger.warning(f"Webhook returned error for token {token[:8]}...: {response.status_code}")
                
    except httpx.TimeoutException:
        await update.message.reply_text(
            "❌ Server javob bermayapti. Iltimos, keyinroq qayta urinib ko'ring."
        )
        logger.error("Timeout while calling webhook")
    except Exception as e:
        await update.message.reply_text(
            "❌ Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."
        )
        logger.error(f"Exception while calling webhook: {str(e)}", exc_info=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

def main():
    """Bot ni ishga tushirish"""
    # Sozlamalarni tekshirish
    validate_config()
    
    try:
        # Application yaratish
        app = Application.builder().token(TOKEN).build()
        
        # Handlerlarni qo'shish
        app.add_handler(CommandHandler("start", start))
        
        # Error handler qo'shish
        app.add_error_handler(error_handler)
        
        # Bot ma'lumotlarini ko'rsatish
        logger.info("=" * 50)
        logger.info("Bot ishga tushmoqda...")
        logger.info(f"Bot username: @{BOT_USERNAME}")
        logger.info(f"Mini App URL: {WEBAPP_URL if WEBAPP_URL else 'Not set'}")
        logger.info(f"Backend: {BACKEND_ORIGIN if BACKEND_ORIGIN else 'Not set'}")
        logger.info("=" * 50)
        
        # Botni ishga tushirish
        app.run_polling(
            drop_pending_updates=True,  # Eski updatelarni tashlab yuborish
            allowed_updates=["message", "callback_query"]  # Faqat kerakli updatelarni qabul qilish
        )
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Bot to'xtatildi (Ctrl+C)")
        sys.exit(0)
    except TelegramError as e:
        logger.error(f"Telegram API xatolik: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

