# Telegram Authentication Endpoint Guide

## Endpoint
**POST** `https://api.mazzaly.uz/api/telegram-auth/`

## Description
This endpoint handles unified authentication for Telegram Mini App users. It automatically:
- **Logs in existing users** by `telegram_id`
- **Creates new users** if they don't exist (auto-signup)
- Returns JWT tokens and user data in a unified format

## Request Format

### Headers
```
Content-Type: application/json
```

### Request Body
```json
{
  "init_data": "query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A279058397%2C%22first_name%22%3A%22John%22%2C%22last_name%22%3A%22Doe%22%2C%22username%22%3A%22johndoe%22%2C%22language_code%22%3A%22en%22%7D&auth_date=1715245600&hash=89d6079ad6762351f38c6dbbc41bb53048019256a9443988af7a48bcad16ba31"
}
```

**Field Description:**
- `init_data` (required): The raw initData string from Telegram WebApp. This contains:
  - `user`: JSON object with telegram user info (id, first_name, last_name, username, etc.)
  - `auth_date`: Unix timestamp of authentication
  - `hash`: HMAC-SHA256 signature for verification
  - Other optional parameters from Telegram

## Success Response (200 OK)

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMwNzUxMjg2LCJpYXQiOjE3MzA3NDc2ODYsImp0aSI6IjEyMzQ1Njc4OTBhYmNkZWYiLCJ1c2VyX2lkIjoxfQ.K7rXY8Z9mN3pQwErTyUiOpAsDfGhJkLzXcVbNm",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTczMDgzNDA4NiwiaWF0IjoxNzMwNzQ3Njg2LCJqdGkiOiJhYmNkZWYxMjM0NTY3ODkwIiwidXNlcl9pZCI6MX0.dGhpc0lzQVJlZnJlc2hUb2tlblNpZ25hdHVyZQ",
  "user": {
    "id": 123,
    "first_name": "John",
    "last_name": "Doe",
    "email": "tg_279058397@telegram.local",
    "telegram_id": "279058397",
    "telegram_username": "johndoe",
    "telegram_first_name": "John",
    "telegram_last_name": "Doe",
    "telegram_photo_url": null,
    "login_method": "telegram",
    "created_via": "telegram",
    "telegram_linked_at": null,
    "last_login_at": "2024-11-03T17:25:00Z",
    "author": null
  }
}
```

## Error Responses

### 400 Bad Request - Invalid Init Data
```json
{
  "detail": "Invalid Telegram authentication hash"
}
```

### 400 Bad Request - Expired Data
```json
{
  "detail": "Telegram authentication data expired"
}
```

### 400 Bad Request - Missing Hash
```json
{
  "detail": "Missing hash in init_data"
}
```

### 400 Bad Request - Invalid User Data
```json
{
  "detail": "Invalid user data"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Server configuration error"
}
```

## cURL Example

### Basic Request
```bash
curl -X POST https://api.mazzaly.uz/api/telegram-auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "init_data": "query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A279058397%2C%22first_name%22%3A%22John%22%2C%22last_name%22%3A%22Doe%22%2C%22username%22%3A%22johndoe%22%2C%22language_code%22%3A%22en%22%7D&auth_date=1730747686&hash=89d6079ad6762351f38c6dbbc41bb53048019256a9443988af7a48bcad16ba31"
  }'
```

### With Verbose Output (for debugging)
```bash
curl -X POST https://api.mazzaly.uz/api/telegram-auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "init_data": "query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A279058397%2C%22first_name%22%3A%22John%22%2C%22last_name%22%3A%22Doe%22%2C%22username%22%3A%22johndoe%22%2C%22language_code%22%3A%22en%22%7D&auth_date=1730747686&hash=89d6079ad6762351f38c6dbbc41bb53048019256a9443988af7a48bcad16ba31"
  }' \
  -v
```

### Testing with Real Telegram WebApp
```javascript
// In your Telegram Mini App
const initData = window.Telegram.WebApp.initData;

fetch('https://api.mazzaly.uz/api/telegram-auth/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ init_data: initData })
})
.then(response => response.json())
.then(data => {
  console.log('Success:', data);
  // Store tokens
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
})
.catch(error => console.error('Error:', error));
```

## Implementation Details

### Code Files
1. **View**: `account/views.py` - `TelegramAuthView`
2. **Service**: `account/telegram_auth_service.py` - `TelegramAuthService`
3. **Serializer**: `account/serializers.py` - `TelegramAuthSerializer`
4. **Utilities**: `auth_telegram/utils.py` - `verify_init_data()`
5. **JWT Service**: `account/jwt_service.py` - `UnifiedJWTService`

### Authentication Flow
```
1. Client sends init_data
2. Server validates init_data signature using TELEGRAM_AUTH_BOT_TOKEN
3. Server checks auth_date is within 24 hours
4. Server extracts telegram_id from user data
5. Server checks if User.objects.filter(telegram_id=...).exists()
   - If YES: Update user info and login
   - If NO: Create new user with get_or_create() and login
6. Server generates JWT tokens using RefreshToken.for_user()
7. Server returns unified response
```

### User Creation Details
- **Email**: Placeholder `tg_{telegram_id}@telegram.local`
- **Password**: Set to unusable (no password authentication)
- **Fields Set**:
  - `telegram_id` (unique identifier)
  - `telegram_username`, `telegram_first_name`, `telegram_last_name`, `telegram_photo_url`
  - `first_name`, `last_name` (from Telegram data)
  - `login_method` = `"telegram"`
  - `created_via` = `"telegram"`
  - `is_email_verified` = `False`
  - `last_login_at` = current timestamp

### Token Generation
Uses `djangorestframework-simplejwt`:
```python
from rest_framework_simplejwt.tokens import RefreshToken

refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)
refresh_token = str(refresh)
```

## Common Bugs & Troubleshooting

### 1. "Invalid Telegram authentication hash"
**Cause**: Wrong bot token or signature mismatch

**Check**:
```bash
# Verify bot token is set correctly
python manage.py shell
>>> from django.conf import settings
>>> print(settings.TELEGRAM_AUTH_BOT_TOKEN)
>>> print(settings.TELEGRAM_BOT_TOKEN)
```

**Fix**:
- Ensure `TELEGRAM_AUTH_BOT_TOKEN` in settings matches the bot token used to generate init_data
- For Mini Apps, use the bot token of the bot associated with the Mini App
- Verify init_data hasn't been modified or corrupted in transit

### 2. "Telegram authentication data expired"
**Cause**: auth_date is older than 24 hours

**Fix**:
- Ensure client sends fresh init_data
- Check system clock on both client and server
- For testing, temporarily increase `max_age` parameter in `verify_init_data()`

### 3. Duplicate user creation
**Cause**: Race condition with concurrent requests

**Fix**: ✅ Already fixed - using `get_or_create()` instead of `get()` + `create()`

### 4. Password validation error
**Cause**: User model requires password, but Telegram users don't have one

**Fix**: ✅ Already fixed - using `set_unusable_password()` for Telegram users

### 5. "Server configuration error"
**Cause**: Missing TELEGRAM_AUTH_BOT_TOKEN or TELEGRAM_BOT_TOKEN

**Check**:
```bash
# In your .env or settings
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_AUTH_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 6. Serializer validation fails
**Cause**: TelegramAuthSerializer requires fields that aren't provided

**Fix**: ✅ Already fixed - serializer only requires `init_data`, no password needed

### 7. Token generation fails
**Cause**: User object is invalid or simplejwt not configured

**Check**:
```python
# settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    # ... other settings
}
```

### 8. "Invalid user data"
**Cause**: Missing or invalid telegram_id in init_data

**Debug**:
```python
# Add logging in TelegramAuthView
import logging
logger = logging.getLogger(__name__)

# Before line 338
logger.debug(f"Parsed telegram_data: {telegram_data}")
```

### 9. Email uniqueness violation
**Cause**: Placeholder email already exists

**Fix**: ✅ Already fixed - using get_or_create() prevents duplicates

### 10. User.DoesNotExist vs IntegrityError
**Cause**: Database race condition

**Fix**: ✅ Already fixed - using atomic transaction with get_or_create()

## Testing Tips

### 1. Generate Test init_data
```python
import hmac
import hashlib
import json
from urllib.parse import urlencode

def create_test_init_data(telegram_id, bot_token):
    import time
    user = {
        'id': telegram_id,
        'first_name': 'Test',
        'last_name': 'User',
        'username': 'testuser'
    }
    
    params = {
        'user': json.dumps(user),
        'auth_date': str(int(time.time()))
    }
    
    # Create data check string
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(params.items()))
    
    # Calculate secret key
    secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
    
    # Calculate hash
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    params['hash'] = hash_value
    return urlencode(params)

# Usage
bot_token = "YOUR_BOT_TOKEN"
init_data = create_test_init_data(123456789, bot_token)
print(init_data)
```

### 2. Test with Django Shell
```python
python manage.py shell

from account.telegram_auth_service import TelegramAuthService

telegram_data = {
    'telegram_id': '123456789',
    'username': 'testuser',
    'first_name': 'Test',
    'last_name': 'User',
    'photo_url': None,
    'auth_date': 1730747686,
    'raw_params': {}
}

user, access, refresh = TelegramAuthService.telegram_login(telegram_data)
print(f"User: {user}")
print(f"Access: {access}")
print(f"Refresh: {refresh}")
```

### 3. Verify Token Works
```bash
# Test access token
curl -X GET https://api.mazzaly.uz/api/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

## Security Notes

1. **Init Data Validation**: Always validated using HMAC-SHA256 signature
2. **Expiration**: init_data expires after 24 hours
3. **Token Security**: Use HTTPS only, store tokens securely
4. **Password**: Telegram users have unusable passwords (cannot login via password)
5. **Email**: Placeholder emails are not verified and cannot receive emails

## Environment Variables Required

```bash
# .env file
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_AUTH_BOT_TOKEN=your_bot_token_here  # Can be same as above
SECRET_KEY=your_django_secret_key
```

## API Integration Example (Python)

```python
import requests

def telegram_auth(init_data: str) -> dict:
    """
    Authenticate with Telegram init_data
    
    Returns:
        dict with 'access', 'refresh', and 'user' keys
    """
    response = requests.post(
        'https://api.mazzaly.uz/api/telegram-auth/',
        json={'init_data': init_data},
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Auth failed: {response.json()}")

# Usage
try:
    result = telegram_auth(init_data)
    access_token = result['access']
    refresh_token = result['refresh']
    user = result['user']
    print(f"Logged in as: {user['first_name']} {user['last_name']}")
except Exception as e:
    print(f"Error: {e}")
```

## Monitoring & Logging

All authentication attempts are logged in `AuthAuditLog`:
```python
from account.models import AuthAuditLog

# View recent attempts
recent_logins = AuthAuditLog.objects.filter(
    action='telegram_login',
    platform='telegram'
).order_by('-created_at')[:10]

for log in recent_logins:
    print(f"{log.created_at}: User {log.user_id}, Success: {log.success}")
```

## Summary of Fixes Applied

1. ✅ Fixed user creation to use `get_or_create()` to prevent duplicates
2. ✅ Added `set_unusable_password()` for Telegram users
3. ✅ Updated UserManager to handle None password properly
4. ✅ Using atomic transactions to prevent race conditions
5. ✅ Proper token generation with simplejwt's `RefreshToken.for_user()`

The endpoint is now production-ready and handles both login and signup automatically! 🚀
