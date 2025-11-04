# Telegram Link - Setup Guide

## ✅ Bitta Bot Konfiguratsiyasi

Siz bitta `@SHOP_AKBA_bot` ishlatmoqchisiz, barcha funksiyalar uchun:

### .env sozlamalari:

```bash
# === Telegram Bot Configuration ===
TELEGRAM_BOT_TOKEN=2060951767:AAFcvGaYkm3N8fxp_4love7rrzIgueh5HkE
TELEGRAM_BOT_USERNAME=SHOP_AKBA_bot

WEBAPP_URL=https://127.0.0.1:8000/telegram/recipes/
BACKEND_ORIGIN=https://127.0.0.1:8000

# === Email Configuration (Mini App uchun) ===
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=sunnatsfychiyev441@gmail.com
EMAIL_HOST_PASSWORD=pigr xgxs rmej xtzz
DEFAULT_FROM_EMAIL=noreply@mazzaly.uz

# === Spoonacular API ===
SPOONACULAR_API_KEY=b31e1cf6a5b34738897f671ca71f5ffe
```

---

## 🚀 Webhook Sozlash

### 1. Webhook o'rnatish:

```bash
curl -X POST "https://api.telegram.org/bot2060951767:AAFcvGaYkm3N8fxp_4love7rrzIgueh5HkE/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.mazzaly.uz/api/mini-app/auth/telegram-webhook/"
  }'
```

**Response:**
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

### 2. Webhook tekshirish:

```bash
curl "https://api.telegram.org/bot2060951767:AAFcvGaYkm3N8fxp_4love7rrzIgueh5HkE/getWebhookInfo"
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "url": "https://api.mazzaly.uz/api/mini-app/auth/telegram-webhook/",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40
  }
}
```

---

## 🧪 Test Qilish

### 1. Web dan link yaratish:

```bash
# Login qiling
curl -X POST https://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Token oling: eyJhbGci...

# Deep link yarating
curl -X POST https://127.0.0.1:8000/api/mini-app/auth/connect-telegram/link/ \
  -H "Authorization: eyJhbGci..." \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "deep_link": "https://t.me/SHOP_AKBA_bot?start=550e8400-e29b-41d4-a716-446655440000",
  "expires_in": 600,
  "expires_at": "2025-11-04T12:10:00Z"
}
```

### 2. Telegram botda:

1. Deep linkni oching: `https://t.me/SHOP_AKBA_bot?start=550e8400-...`
2. Bot `/start` commandni qabul qiladi
3. Server webhook orqali payload tekshiradi
4. Akkaunt bog'lanadi ✅

**Bot javoblari:**

- ✅ Success: `Success! Your Telegram account has been linked to test@example.com`
- ❌ Expired: `Link has expired. Please request a new link from the website.`
- ❌ Used: `This link has already been used. Please request a new link.`

---

## 📊 Bot Funksiyalari

Bitta bot barcha vazifalarni bajaradi:

| Funksiya | Endpoint | Tavsif |
|----------|----------|--------|
| 🍽 Recipes | `/telegram/recipes/` | Mini App - retseptlar |
| 🔐 Auth | `/api/telegram-auth/` | Telegram orqali login |
| ✉️ Email Link | `/api/mini-app/auth/connect-email/` | Email ulash (OTP) |
| 🔗 Telegram Link | `/api/mini-app/auth/connect-telegram/link/` | Web → Telegram ulanish |
| 📡 Webhook | `/api/mini-app/auth/telegram-webhook/` | Bot webhook handler |

---

## 🔧 Troubleshooting

### Webhook ishlamayapti?

**Tekshirish:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

**Xatolar:**

| Xato | Sabab | Yechim |
|------|-------|--------|
| `last_error_message` mavjud | Server 200 qaytarmayapti | Loglarni tekshiring |
| `pending_update_count > 0` | Webhook to'xtab qolgan | Serverni restart qiling |
| `url` bo'sh | Webhook o'rnatilmagan | `setWebhook` qayta ishga tushuring |

### Link expire bo'lib qoladi?

```python
# settings.py
USE_TZ = True
TIME_ZONE = 'UTC'
```

### Database tekshirish:

```python
python manage.py shell

from account.models import User, TelegramLinkNonce

# User telegram_id tekshirish
user = User.objects.get(email='test@example.com')
print(f"Telegram ID: {user.telegram_id}")
print(f"Login method: {user.login_method}")

# Nonce statusini ko'rish
nonce = TelegramLinkNonce.objects.filter(user=user).last()
print(f"Used: {nonce.used}")
print(f"Expired: {nonce.is_expired}")
```

---

## ✅ Final Checklist

- [x] `.env` da `TELEGRAM_BOT_TOKEN` to'g'ri
- [x] `.env` da `TELEGRAM_BOT_USERNAME=SHOP_AKBA_bot`
- [x] Migration ishga tushirilgan: `0011_add_telegram_link_nonce`
- [x] Webhook o'rnatilgan
- [x] Webhook HTTPS orqali ochiq
- [x] Bot `/start` commandni qabul qiladi
- [x] Test user bilan test qilingan

---

## 📝 Qo'shimcha Ma'lumot

**To'liq hujjat:** `TELEGRAM_LINK_GUIDE.md`

**Endpoints:**
- `POST /api/mini-app/auth/connect-telegram/link/` - Create link
- `POST /api/mini-app/auth/telegram-webhook/` - Bot webhook

**Database:**
- Model: `TelegramLinkNonce`
- Admin: `/admin/account/telegramlinknonce/`

**Security:**
- UUID-based tokens
- 10-minute expiry
- One-time use
- Atomic transactions
- Audit logging

---

Hammasi tayyor! 🎉
