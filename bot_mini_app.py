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

# Bot token .env fayilidan mini_app_bot_t nomi bilan olinadi
TOKEN = (os.getenv("mini_app_bot_t") or "").strip()
WEBAPP_URL = (os.getenv("WEBAPP_main_URL") or "").strip()
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
        errors.append("mini_app_bot_t missing. .env fayiliga mini_app_bot_t=YOUR_BOT_TOKEN qo'shing.")
    elif not valid_token(TOKEN):
        errors.append("mini_app_bot_t invalid format. Token formati: 123456:ABC-DEF...")
    
    # WEBAPP_URL tekshiruvi
    if not WEBAPP_URL:
        warnings.append("WEBAPP_main_URL not set. Mini App button won't work.")
    elif not WEBAPP_URL.startswith("https://"):
        warnings.append("WEBAPP_main_URL must start with https://")
    
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
                "WEBAPP_main_URL ni .env fayiliga qo'shing:\n"
                "WEBAPP_main_URL=https://your-domain.com/telegram/test-init-data/"
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
    """Token tekshirish va backend ga yuborish"""
    import httpx
    
    user = update.effective_user
    telegram_id = str(user.id) if user else None
    username = user.username if user else ''
    
    if not telegram_id:
        await update.message.reply_text("❌ Telegram user ID topilmadi.")
        return
    
    if not BACKEND_ORIGIN or not BOT_INTERNAL_SECRET:
        await update.message.reply_text(
            "❌ Server sozlamalari to'liq emas. Iltimos, administrator bilan bog'laning."
        )
        logger.error("BACKEND_ORIGIN yoki BOT_INTERNAL_SECRET sozlanmagan")
        return
    
    try:
        # Backend ga token tekshirish so'rovi yuborish
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BACKEND_ORIGIN}/api/telegram/link/confirm/",
                json={
                    "token": token,
                    "telegram_id": telegram_id,
                    "username": username
                },
                headers={
                    "Authorization": f"Bearer {BOT_INTERNAL_SECRET}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                await update.message.reply_text(
                    "✅ Hisobingiz muvaffaqiyatli Telegram akkauntiga ulandi!"
                )
                logger.info(f"Successfully linked Telegram ID {telegram_id} using token {token[:8]}...")
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('detail', 'Hisobni ulashda xatolik yuz berdi')
                await update.message.reply_text(f"❌ {error_msg}")
                logger.warning(f"Failed to link Telegram ID {telegram_id}: {error_msg}")
            elif response.status_code == 404:
                await update.message.reply_text(
                    "❌ Bu link eskirgan yoki noto'g'ri. Iltimos, veb-saytdan yangi link oling."
                )
                logger.warning(f"Invalid or expired token: {token[:8]}...")
            else:
                await update.message.reply_text(
                    "❌ Hisobni ulashda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."
                )
                logger.error(f"Unexpected error linking account: {response.status_code} - {response.text}")
                
    except httpx.TimeoutException:
        await update.message.reply_text(
            "❌ Server javob bermayapti. Iltimos, keyinroq qayta urinib ko'ring."
        )
        logger.error("Timeout while linking account")
    except Exception as e:
        await update.message.reply_text(
            "❌ Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."
        )
        logger.error(f"Exception while linking account: {str(e)}", exc_info=True)


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
        logger.info(f"Bot username: @SHOP_AKBAR_bot")
        logger.info(f"Mini App URL: {WEBAPP_URL if WEBAPP_URL else 'Not set'}")
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

