# Telegram Link Guide

Web saytdan Telegram botga akkaunt ulanish (link) funksiyasi.

## 🎯 Maqsad

Foydalanuvchi web saytga kirganda "Link Telegram" tugmasini bosib, Telegram bot orqali akkauntini bog'lashi mumkin. Shundan keyin:
- ✅ Web saytga email+password bilan
- ✅ Telegram botga telegram_id bilan

**Bir vaqtning o'zida** kirishga imkon beradi.

---

## 📋 Ish jarayoni (Flow)

```
1. User web saytga kiradi (JWT token bor)
   ↓
2. "Link Telegram" tugmasini bosadi
   ↓
3. POST /api/mini-app/auth/connect-telegram/link/
   Server deep link yaratadi: t.me/mazzaly_bot?start=ABC123
   ↓
4. User Telegram botni ochadi
   ↓
5. Bot /start ABC123 qabul qiladi
   ↓
6. Webhook: POST /api/mini-app/auth/telegram-webhook/
   Server payload tekshiradi va akkauntni bog'laydi
   ↓
7. ✅ User.telegram_id = "123456789" saqlanadi
   ✅ User.login_method = "both" o'zgaradi
```

---

## ⚙️ Sozlash

### 1. .env ga qo'shing:

```bash
# === Telegram Bot Configuration ===
# Bitta bot barcha funksiyalar uchun (recipes, auth, mini-app, linking)
TELEGRAM_BOT_TOKEN=2060951767:AAFcvGaYkm3N8fxp_4love7rrzIgueh5HkE
TELEGRAM_BOT_USERNAME=SHOP_AKBA_bot
```

**Eslatma:** Siz bitta bot ishlatmoqchisiz, shuning uchun `TELEGRAM_BOT_TOKEN` barcha funksiyalar uchun ishlatiladi:
- Recipes bot (yangi retsept e'lonlari)
- Auth/Login (Telegram orqali kirish)
- Mini App (email linking)
- Web-to-Telegram linking (bu yangi funksiya)

### 2. Bot webhookni sozlang:

```bash
# BotFather orqali bot yarating va tokenni oling
# Keyin webhook o'rnating:

curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
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

### 3. Webhook tekshirish:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

---

## 🔌 API Endpoints

### 1. POST `/api/mini-app/auth/connect-telegram/link/`

**Web saytdan deep link yaratish**

**Headers:**
```
Authorization: <JWT_ACCESS_TOKEN>
```

**Request:**
```json
{}
```

**Response (200):**
```json
{
  "deep_link": "https://t.me/SHOP_AKBA_bot?start=550e8400-e29b-41d4-a716-446655440000",
  "expires_in": 600,
  "expires_at": "2025-11-04T12:10:00Z"
}
```

**Errors:**
- `400`: User allaqachon Telegram bilan bog'langan
- `401`: Token yo'q yoki noto'g'ri

---

### 2. POST `/api/mini-app/auth/telegram-webhook/`

**Telegram bot webhook (Telegram serverlar chaqiradi)**

**Request (Telegram yuboradi):**
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 456,
    "from": {
      "id": 123456789,
      "first_name": "John",
      "last_name": "Doe",
      "username": "johndoe"
    },
    "text": "/start 550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Response:**
```json
{
  "ok": true
}
```

**Bot javoblari:**

| Holat | Bot xabari |
|-------|------------|
| ✅ Muvaffaqiyatli | `✅ Success! Your Telegram account has been linked to user@example.com. You can now access Mazzaly from both web and Telegram!` |
| ❌ Link expired | `❌ Link has expired. Please request a new link from the website.` |
| ❌ Already used | `❌ This link has already been used. Please request a new link.` |
| ❌ Already linked | `ℹ️ Your account is already linked to Telegram (ID: 123456789).` |
| ❌ Telegram ID busy | `❌ This Telegram account is already linked to another user.` |

---

## 🧪 Test qilish

### 1. Web dan link yaratish:

```bash
# Avval login qiling va token oling
curl -X POST https://api.mazzaly.uz/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Response: { "access": "eyJhbGci...", ... }

# Deep link yarating
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/connect-telegram/link/ \
  -H "Authorization: eyJhbGci..." \
  -H "Content-Type: application/json"

# Response:
# {
#   "deep_link": "https://t.me/SHOP_AKBA_bot?start=550e8400-e29b-41d4-a716-446655440000",
#   "expires_in": 600,
#   "expires_at": "2025-11-04T12:10:00Z"
# }
```

### 2. Telegram botda test:

1. Deep linkni Telegram da oching
2. Bot `/start` xabarini qabul qiladi
3. Server webhook orqali payload tekshiradi
4. Bot tasdiq xabarini yuboradi

### 3. Database tekshirish:

```python
# Django shell
python manage.py shell

from account.models import User, TelegramLinkNonce

# User telegram_id borligini tekshir
user = User.objects.get(email='user@example.com')
print(user.telegram_id)  # "123456789"
print(user.login_method)  # "both"

# Nonce ishlatilganini tekshir
nonce = TelegramLinkNonce.objects.filter(user=user).last()
print(nonce.used)  # True
print(nonce.telegram_user_id)  # "123456789"
```

---

## 🔒 Xavfsizlik

### 1. Nonce (One-time token)
- ✅ UUID format
- ✅ Unique (database constraint)
- ✅ 10 daqiqa amal qiladi
- ✅ Bir marta ishlatiladi
- ✅ Expiration tekshiriladi

### 2. Payload validation
```python
# Views da:
1. UUID format tekshirish
2. Database mavjudligini tekshir
3. Expiration tekshir
4. Used flagini tekshir
5. Faqat keyin akkauntni bog'la
```

### 3. Duplicate prevention
- ✅ User allaqachon telegram_id ga ega bo'lsa - rad etish
- ✅ Telegram ID boshqa userda bo'lsa - rad etish
- ✅ Link expire bo'lganda - yangi so'rash

### 4. Audit logging
```python
# Barcha harakatlar log qilinadi:
- telegram_link_requested (web)
- telegram_linked (bot)
```

---

## 🗄️ Database Models

### TelegramLinkNonce

```python
class TelegramLinkNonce(models.Model):
    user = ForeignKey(User)              # Qaysi user
    nonce = UUIDField(unique=True)       # Link tokeni
    created_at = DateTimeField()         # Yaratilgan vaqt
    expires_at = DateTimeField()         # 10 min keyin
    used = BooleanField(default=False)   # Ishlatilganmi
    used_at = DateTimeField()            # Qachon ishlatilgan
    telegram_user_id = CharField()       # Qaysi telegram user bog'lagan
```

**Indexes:**
- `(nonce, used)` - Tez qidiruv
- `(user, expires_at)` - User bo'yicha filter

---

## 📊 Frontend Integration

### React Example:

```javascript
// 1. Link yaratish
async function createTelegramLink() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('https://api.mazzaly.uz/api/mini-app/auth/connect-telegram/link/', {
    method: 'POST',
    headers: {
      'Authorization': token,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Open deep link
    window.open(data.deep_link, '_blank');
    
    // Show countdown
    console.log(`Link expires in ${data.expires_in} seconds`);
  } else {
    alert(data.detail);
  }
}

// 2. "Link Telegram" tugmasi
<button onClick={createTelegramLink}>
  <TelegramIcon />
  Link Telegram Account
</button>

// 3. Status ko'rsatish
{user.telegram_id && (
  <div className="linked-badge">
    ✅ Linked to Telegram
  </div>
)}
```

---

## 🐛 Troubleshooting

### 1. Webhook ishlamayapti

**Tekshirish:**
```bash
# Webhook info
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Last error ko'rish
# Response da "last_error_message" field bor
```

**Umumiy xatolar:**
- ❌ SSL sertifikat muammosi - HTTPS ishlatish kerak
- ❌ Webhook URL unreachable - Server ochiqmi?
- ❌ Token noto'g'ri - .env tekshir

### 2. Link expire bo'lib qoladi

**Sabab:**
- Foydalanuvchi 10 daqiqada botni ochmagan
- Server vaqti noto'g'ri sozlangan

**Yechim:**
```python
# settings.py
USE_TZ = True
TIME_ZONE = 'UTC'
```

### 3. "Already linked" xatosi

**Tekshirish:**
```python
# Django shell
user = User.objects.get(email='...')
print(user.telegram_id)

# Agar noto'g'ri bo'lsa - tozalash
user.telegram_id = None
user.login_method = 'email'
user.save()
```

---

## 📈 Monitoring

### Audit logs tekshirish:

```python
from account.models import AuthAuditLog

# Link so'rovlari
links_requested = AuthAuditLog.objects.filter(
    action='telegram_link_requested'
).count()

# Muvaffaqiyatli bog'langanlar
links_completed = AuthAuditLog.objects.filter(
    action='telegram_linked',
    success=True
).count()

# Conversion rate
rate = (links_completed / links_requested) * 100
print(f"Link conversion: {rate:.1f}%")
```

### Admindan ko'rish:

```
/admin/account/telegramlinknonce/
```

Filtrlar:
- Used: Yes/No
- Expires: Today, This week
- User: Search by email

---

## ✅ Checklist

- [ ] `.env` da `TELEGRAM_BOT_TOKEN` sozlangan
- [ ] `.env` da `TELEGRAM_BOT_USERNAME` sozlangan
- [ ] Webhook o'rnatilgan (`setWebhook`)
- [ ] Webhook HTTPS orqali ochiq
- [ ] Migration run qilingan
- [ ] Bot `/start` commandni qabul qiladi
- [ ] Frontend "Link Telegram" tugmasi bor
- [ ] Test user bilan test qilingan

---

## 🎉 Summary

### Implemented Features:

✅ Deep link generation (UUID-based)  
✅ One-time use tokens  
✅ 10-minute expiration  
✅ Telegram webhook handler  
✅ Automatic account linking  
✅ Duplicate prevention  
✅ Audit logging  
✅ Swagger documentation  
✅ Admin interface  
✅ Security best practices  

### Endpoints:

1. `POST /api/mini-app/auth/connect-telegram/link/` - Create link (JWT auth)
2. `POST /api/mini-app/auth/telegram-webhook/` - Webhook (AllowAny)

### Database:

- `TelegramLinkNonce` model with indexes
- Migration: `0011_add_telegram_link_nonce.py`

**Production ready!** 🚀
