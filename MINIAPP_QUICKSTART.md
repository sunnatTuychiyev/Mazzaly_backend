# Mini App Email Connection - Quick Start

## 🚀 Quick Setup

### 1. Run Migrations
```bash
python manage.py makemigrations account
python manage.py migrate account
```

### 2. Configure Email Settings
Add to `.env` or `settings.py`:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@mazzaly.uz
```

### 3. Test the Endpoints
```bash
# Run tests
python manage.py test account.test_miniapp_email_connect

# Start server
python manage.py runserver
```

---

## 📋 API Quick Reference

### Endpoint 1: Connect Email
```bash
POST /api/mini-app/auth/connect-email/

# With Bearer token
curl -X POST http://localhost:8000/api/mini-app/auth/connect-email/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123"}'

# With telegram_id
curl -X POST http://localhost:8000/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123", "telegram_id": "123456789"}'
```

### Endpoint 2: Verify OTP
```bash
POST /api/mini-app/auth/OTP/

curl -X POST http://localhost:8000/api/mini-app/auth/OTP/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "otp": "123456"}'
```

---

## 🔑 Key Features

✅ **Dual Auth**: Bearer token OR telegram_id  
✅ **Auto-Signup**: Creates user if doesn't exist  
✅ **Secure OTP**: 6-digit code, 10min expiry, hashed storage  
✅ **Password Validation**: 8+ chars, uppercase, lowercase, digit  
✅ **Rate Limiting**: 3/hour (connect), 10/hour (verify)  
✅ **Simultaneous Login**: Telegram + Email/Password both work  

---

## 🔒 Security

| Feature | Implementation |
|---------|---------------|
| OTP Storage | SHA-256 hash |
| Password Storage | PBKDF2-SHA256 (Django default) |
| OTP Expiry | 10 minutes |
| Max Attempts | 5 per OTP |
| Rate Limit | IP-based throttling |

---

## 📊 Response Formats

### Success (connect-email)
```json
{
  "status": "otp_sent",
  "email": "user@example.com",
  "detail": "OTP sent to email"
}
```

### Success (verify OTP)
```json
{
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci...",
  "user": {
    "id": 42,
    "email": "user@example.com",
    "telegram_id": "123456789",
    "login_method": "both",
    "is_email_verified": true
  }
}
```

### Errors
```json
// 400 - Validation error
{"detail": "Password must be at least 8 characters long"}

// 400 - Invalid OTP
{"detail": "Invalid OTP. 4 attempts remaining.", "attempts_remaining": 4}

// 401 - Invalid token
{"detail": "Invalid or expired token"}

// 404 - No OTP found
{"detail": "No pending verification found for this email"}

// 429 - Rate limit
{"detail": "Request was throttled. Expected available in 3600 seconds."}
```

---

## 🧪 Testing

### Run All Tests
```bash
python manage.py test account.test_miniapp_email_connect -v 2
```

### Test Coverage
```bash
coverage run --source='account' manage.py test account.test_miniapp_email_connect
coverage report -m
coverage html  # Generate HTML report
```

### Manual Test Flow
```bash
# 1. Connect email (creates user + sends OTP)
curl -X POST http://localhost:8000/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123","telegram_id":"999"}'

# 2. Check email inbox for OTP

# 3. Verify OTP
curl -X POST http://localhost:8000/api/mini-app/auth/OTP/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp":"YOUR_OTP"}'

# 4. Test token works
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer ACCESS_TOKEN_FROM_STEP3"

# 5. Test email login works
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'
```

---

## 📁 Files Created

```
account/
├── models.py                          # Updated EmailOTPTelegramLink model
├── serializers.py                     # Added MiniApp serializers
├── miniapp_views.py                   # NEW: View implementations
├── urls.py                           # Added miniapp routes
├── test_miniapp_email_connect.py     # NEW: Comprehensive tests
└── migrations/
    └── 00XX_update_emailotptelegramlink.py  # Auto-generated
```

---

## 🐛 Common Issues

**OTP not received?**
- Check spam folder
- Verify EMAIL_HOST settings
- Check Django logs: `tail -f logs/django.log`

**"Invalid token"?**
- Token expired (60min default)
- Use /api/token/refresh/ endpoint

**Rate limit hit?**
- Wait 1 hour or adjust throttle settings
- In development: disable throttling temporarily

**Email already taken?**
- Email belongs to another telegram_id
- Use different email or contact support

---

## 📚 Documentation

- **Full API Docs**: `MINIAPP_EMAIL_CONNECTION_API.md`
- **Telegram Auth Guide**: `TELEGRAM_AUTH_GUIDE.md`
- **Tests**: `test_miniapp_email_connect.py`

---

## 🎯 Next Steps

1. **Run migrations** to update database schema
2. **Configure email** settings in production
3. **Test endpoints** with curl or Postman
4. **Integrate frontend** using JavaScript examples
5. **Monitor logs** for errors and usage patterns
6. **Adjust rate limits** based on actual traffic

---

## 💡 Pro Tips

- Use Bearer token mode when possible (more secure)
- Implement OTP retry UI with countdown timer
- Show password strength indicator on frontend
- Log all auth attempts for security auditing
- Consider SMS backup for OTP delivery
- Cache OTP sending to prevent spam

---

## 🔗 Related Endpoints

- `POST /api/telegram-auth/` - Telegram login
- `POST /api/login/` - Email/password login
- `POST /api/token/refresh/` - Refresh access token
- `GET /api/profile/` - Get user profile

Both Telegram and email login return tokens in same format! 🎉
