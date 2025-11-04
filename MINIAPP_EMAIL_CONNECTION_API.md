# Mini App Email Connection API

Complete documentation for connecting email+password to Telegram-based Mini App accounts.

## Table of Contents
- [Overview](#overview)
- [Endpoints](#endpoints)
- [Authentication Modes](#authentication-modes)
- [Request/Response Examples](#requestresponse-examples)
- [Edge Cases & Security](#edge-cases--security)
- [Settings Configuration](#settings-configuration)
- [Testing](#testing)

---

## Overview

These endpoints allow Telegram Mini App users to link an email+password to their account, enabling simultaneous login via:
1. **Telegram Mini App** (telegram_id based)
2. **Website/Mobile App** (email+password based)

### Flow
```
1. User requests to connect email → OTP sent to email
2. User enters OTP → Email verified, password set, JWT tokens returned
3. User can now login via both Telegram and email+password
```

---

## Endpoints

### 1. POST /api/mini-app/auth/connect-email/

**Purpose**: Initiate email connection by sending OTP

**Authentication**: Either Bearer token OR telegram_id in body (at least one required)

**Rate Limit**: 3 requests/hour per IP

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "telegram_id": "123456789"  // Required if no Bearer token
}
```

**Success Response (200 OK)**:
```json
{
  "status": "otp_sent",
  "email": "user@example.com",
  "detail": "OTP sent to email"
}
```

**Error Responses**:
- `400` - Validation errors, missing fields, duplicate email
- `401` - Invalid Bearer token
- `429` - Rate limit exceeded
- `500` - Failed to send email

---

### 2. POST /api/mini-app/auth/OTP/

**Purpose**: Verify OTP and complete email linking

**Authentication**: None required

**Rate Limit**: 10 requests/hour per IP

**Request Body**:
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Success Response (200 OK)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 42,
    "first_name": "John",
    "last_name": "Doe",
    "email": "user@example.com",
    "telegram_id": "123456789",
    "telegram_username": "johndoe",
    "login_method": "both",
    "created_via": "telegram",
    "is_email_verified": true
  }
}
```

**Error Responses**:
- `400` - Invalid OTP, expired OTP, validation errors
- `404` - No pending verification found for email
- `429` - Too many failed attempts (max 5)

---

## Authentication Modes

### Mode 1: Bearer Token (Recommended)

User already logged in via Telegram, has access token.

```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

**Advantages**:
- More secure (authenticated request)
- No need to pass telegram_id
- Validated against actual user session

### Mode 2: Telegram ID in Body

User not authenticated, provides telegram_id directly.

```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "telegram_id": "123456789"
  }'
```

**Use Cases**:
- First-time user with no token yet
- Simplified integration
- Auto-signup flow

---

## Request/Response Examples

### Example 1: Complete Flow with Bearer Token

**Step 1: Request OTP**
```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "alice@example.com",
    "password": "MySecure123Pass"
  }'
```

**Response**:
```json
{
  "status": "otp_sent",
  "email": "alice@example.com",
  "detail": "OTP sent to email"
}
```

**Step 2: User receives email with OTP (e.g., "456789")**

**Step 3: Verify OTP**
```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/OTP/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "otp": "456789"
  }'
```

**Response**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMwNzU1NjAwLCJpYXQiOjE3MzA3NTIwMDAsImp0aSI6ImFiY2RlZjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjo0Mn0.signature",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTczMDgzODQwMCwiaWF0IjoxNzMwNzUyMDAwLCJqdGkiOiIxMjM0NTY3ODkwYWJjZGVmIiwidXNlcl9pZCI6NDJ9.signature",
  "user": {
    "id": 42,
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice@example.com",
    "telegram_id": "987654321",
    "telegram_username": "alice_smith",
    "login_method": "both",
    "created_via": "telegram",
    "is_email_verified": true,
    "telegram_linked_at": "2024-11-04T00:00:00Z"
  }
}
```

---

### Example 2: Auto-Signup Flow (New User)

**Request OTP for new telegram_id**:
```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "BobSecure456",
    "telegram_id": "555666777"
  }'
```

**Response**:
```json
{
  "status": "otp_sent",
  "email": "bob@example.com",
  "detail": "OTP sent to email"
}
```

**Note**: User with `telegram_id=555666777` is automatically created in the background.

---

### Example 3: Error Cases

**Invalid Password (too short)**:
```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "weak",
    "telegram_id": "123456"
  }'
```

**Response (400)**:
```json
{
  "password": [
    "Password must be at least 8 characters long"
  ]
}
```

**Email Already Taken**:
```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "taken@example.com",
    "password": "SecurePass123",
    "telegram_id": "123456"
  }'
```

**Response (400)**:
```json
{
  "detail": "This email is already registered to another account"
}
```

**Invalid OTP**:
```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/OTP/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp": "000000"
  }'
```

**Response (400)**:
```json
{
  "detail": "Invalid OTP. 4 attempts remaining.",
  "attempts_remaining": 4
}
```

**Expired OTP**:
```bash
curl -X POST https://api.mazzaly.uz/api/mini-app/auth/OTP/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp": "123456"
  }'
```

**Response (400)**:
```json
{
  "detail": "OTP has expired. Please request a new one."
}
```

---

## Edge Cases & Security

### 1. OTP Security
- **Storage**: OTPs are stored as SHA-256 hashes, never plaintext
- **Expiry**: 10 minutes from creation
- **Attempts**: Maximum 5 failed attempts before OTP is locked
- **Single Use**: OTP is marked as verified after successful use

### 2. Password Security
- **Requirements**:
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
- **Storage**: Passwords are hashed using Django's `make_password` (PBKDF2-SHA256)
- **Temporary Storage**: Password hash stored in OTP record until verification

### 3. Rate Limiting
- **Connect Email**: 3 requests/hour per IP address
- **Verify OTP**: 10 requests/hour per IP address
- **Per-OTP Limit**: 5 verification attempts per OTP

### 4. Duplicate Prevention
- **Email Uniqueness**: Prevents email from being linked to multiple accounts
- **Idempotency**: Requesting OTP multiple times invalidates previous OTPs
- **Race Conditions**: Uses `get_or_create` with database-level unique constraints

### 5. Auto-Signup Logic
- **Trigger**: If telegram_id doesn't exist in database
- **User Creation**:
  - `telegram_id`: From request
  - `email`: Placeholder `tg_{telegram_id}@telegram.local`
  - `password`: Set to unusable (no password auth initially)
  - `login_method`: `"telegram"`
  - `created_via`: `"telegram"`
- **Email Update**: Placeholder email replaced with real email after OTP verification

### 6. Simultaneous Login Support
After email linking:
- **Telegram Login**: Still works with `telegram_id` via `/api/telegram-auth/`
- **Email Login**: Now works with `email+password` via `/api/login/`
- **Token Interoperability**: JWT tokens work for both login methods
- **User State**: `login_method` automatically updates to `"both"`

### 7. Edge Case Handling

| Scenario | Behavior |
|----------|----------|
| User requests OTP twice | Previous OTP invalidated, new one created |
| User tries different emails | Each email gets separate OTP record |
| User enters wrong OTP 5 times | Must request new OTP (old one locked) |
| OTP expires | Must request new OTP |
| Email already used by other user | Returns 400 error, linking prevented |
| Telegram user without real email | Placeholder email stored until linking |
| Bearer token expired during flow | Returns 401, user must re-authenticate |

### 8. Data Integrity
- **Atomic Transactions**: Email linking happens in single transaction
- **Rollback on Error**: If JWT generation fails, user data isn't updated
- **Audit Logging**: All attempts logged in `AuthAuditLog` table
- **Email Verification Flag**: `is_email_verified=True` only after OTP verification

---

## Settings Configuration

### Required Settings

Add to `settings.py` or `.env`:

```python
# Email Configuration (for sending OTPs)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@mazzaly.uz'

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Throttling (optional, custom rates)
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    }
}
```

### Environment Variables (.env)

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@mazzaly.uz

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

---

## Testing

### Run Tests

```bash
# Run all mini-app email connection tests
python manage.py test account.test_miniapp_email_connect

# Run specific test class
python manage.py test account.test_miniapp_email_connect.MiniAppConnectEmailTests

# Run with coverage
coverage run --source='account' manage.py test account.test_miniapp_email_connect
coverage report
```

### Test Coverage

The test suite covers:
- ✅ Happy path (both authentication modes)
- ✅ Auto-signup for new users
- ✅ Password validation
- ✅ Email uniqueness checks
- ✅ Invalid/expired OTP handling
- ✅ Attempts limiting
- ✅ Token generation and user updates
- ✅ Simultaneous login capability
- ✅ Security features (hashing, rate limiting)
- ✅ Idempotency
- ✅ Email sending failures

### Manual Testing with cURL

**1. Connect Email (with telegram_id)**:
```bash
curl -v -X POST http://localhost:8000/api/mini-app/auth/connect-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "telegram_id": "123456789"
  }'
```

**2. Check email inbox for OTP**

**3. Verify OTP**:
```bash
curl -v -X POST http://localhost:8000/api/mini-app/auth/OTP/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "YOUR_OTP_HERE"
  }'
```

**4. Use returned access token**:
```bash
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**5. Test email+password login**:
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'
```

---

## Database Models

### EmailOTPTelegramLink

```python
class EmailOTPTelegramLink(models.Model):
    user = ForeignKey(User, on_delete=CASCADE, null=True, blank=True)
    email = EmailField()
    code_hash = CharField(max_length=128)  # SHA-256 hash of OTP
    password = CharField(max_length=128)   # Hashed password (PBKDF2)
    telegram_id = CharField(max_length=64, db_index=True)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()  # created_at + 10 minutes
    attempts = IntegerField(default=0)  # Failed verification attempts
    verified_at = DateTimeField(null=True, blank=True)  # Null until verified
```

**Indexes**:
- `(email, telegram_id)`
- `(telegram_id, expires_at)`
- `(email, expires_at)`

---

## Migration

Create and run migrations for the updated model:

```bash
# Create migrations
python manage.py makemigrations account

# Apply migrations
python manage.py migrate account
```

**Expected Migration**:
```python
# Generated migration file
operations = [
    migrations.AddField(
        model_name='emailotptelegramlink',
        name='user',
        field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='email_otp_links', to=settings.AUTH_USER_MODEL),
    ),
    migrations.AddField(
        model_name='emailotptelegramlink',
        name='code_hash',
        field=models.CharField(max_length=128),
    ),
    migrations.AddField(
        model_name='emailotptelegramlink',
        name='password',
        field=models.CharField(max_length=128),
    ),
    migrations.RemoveField(
        model_name='emailotptelegramlink',
        name='code',
    ),
]
```

---

## API Integration Examples

### JavaScript (Telegram Mini App)

```javascript
// Step 1: Connect email
async function connectEmail(email, password) {
  // Get access token from Telegram login
  const accessToken = localStorage.getItem('access_token');
  
  const response = await fetch('https://api.mazzaly.uz/api/mini-app/auth/connect-email/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    console.log('OTP sent to:', data.email);
    return data;
  } else {
    throw new Error(data.detail || 'Failed to send OTP');
  }
}

// Step 2: Verify OTP
async function verifyOTP(email, otp) {
  const response = await fetch('https://api.mazzaly.uz/api/mini-app/auth/OTP/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, otp })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store new tokens
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    console.log('Email connected successfully!', data.user);
    return data;
  } else {
    throw new Error(data.detail || 'Invalid OTP');
  }
}

// Usage
try {
  await connectEmail('user@example.com', 'SecurePass123');
  // Show OTP input form
  const otp = prompt('Enter OTP sent to your email');
  const result = await verifyOTP('user@example.com', otp);
  console.log('Success!', result.user);
} catch (error) {
  console.error('Error:', error.message);
}
```

### Python (requests)

```python
import requests

BASE_URL = 'https://api.mazzaly.uz/api'

def connect_email(email, password, access_token=None, telegram_id=None):
    """Request OTP for email connection."""
    headers = {'Content-Type': 'application/json'}
    data = {'email': email, 'password': password}
    
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    elif telegram_id:
        data['telegram_id'] = telegram_id
    else:
        raise ValueError('Either access_token or telegram_id required')
    
    response = requests.post(
        f'{BASE_URL}/mini-app/auth/connect-email/',
        headers=headers,
        json=data
    )
    response.raise_for_status()
    return response.json()

def verify_otp(email, otp):
    """Verify OTP and get tokens."""
    response = requests.post(
        f'{BASE_URL}/mini-app/auth/OTP/',
        headers={'Content-Type': 'application/json'},
        json={'email': email, 'otp': otp}
    )
    response.raise_for_status()
    return response.json()

# Usage
try:
    # With telegram_id
    result = connect_email(
        email='user@example.com',
        password='SecurePass123',
        telegram_id='123456789'
    )
    print(f"OTP sent to {result['email']}")
    
    otp = input('Enter OTP: ')
    auth_result = verify_otp('user@example.com', otp)
    
    print(f"Access token: {auth_result['access']}")
    print(f"User: {auth_result['user']}")
except requests.HTTPError as e:
    print(f"Error: {e.response.json()}")
```

---

## Troubleshooting

### Common Issues

**1. "Failed to send OTP"**
- Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings
- Verify SMTP server is reachable
- Check email service quotas/limits
- Look at Django logs for SMTP errors

**2. "Invalid or expired token"**
- Token might be expired (default 60 minutes)
- Use refresh token endpoint to get new access token
- Re-authenticate via telegram-auth if refresh token expired

**3. "This email is already registered"**
- Email belongs to different telegram_id
- User should use different email or contact support
- Check if this is intentional (prevent account hijacking)

**4. "Too many failed attempts"**
- User exceeded 5 OTP verification attempts
- Must request new OTP
- Implement delay/backoff on frontend

**5. OTP not received**
- Check spam folder
- Verify email address is correct
- Check email service logs
- Try resending (invalidates old OTP)

---

## Summary

### Key Features
✅ Dual authentication mode (Bearer token or telegram_id)  
✅ Auto-signup for new Telegram users  
✅ Secure OTP generation and storage (hashed)  
✅ Password strength validation  
✅ Rate limiting and attempts tracking  
✅ Simultaneous login support (Telegram + Email)  
✅ Idempotent OTP requests  
✅ Comprehensive error handling  
✅ Audit logging  
✅ Full test coverage  

### Security Highlights
🔒 OTPs stored as SHA-256 hashes  
🔒 Passwords hashed with PBKDF2-SHA256  
🔒 10-minute OTP expiry  
🔒 5 attempt limit per OTP  
🔒 Rate limiting on both endpoints  
🔒 Email uniqueness enforcement  
🔒 Atomic database transactions  

The implementation is production-ready and follows Django/DRF best practices! 🚀
