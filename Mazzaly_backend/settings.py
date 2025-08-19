from pathlib import Path
from decouple import config
from datetime import timedelta
import re

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === Required environment variables ===
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="").strip()
WEBAPP_URL = config("WEBAPP_URL", default="").strip()
BACKEND_ORIGIN = config("BACKEND_ORIGIN", default="").strip()
FRONTEND_ORIGIN = config("FRONTEND_ORIGIN", default=BACKEND_ORIGIN).strip()
SECRET_KEY = config("SECRET_KEY", default="").strip()

if not re.fullmatch(r"\d{6,12}:[A-Za-z0-9_-]{30,}", TELEGRAM_BOT_TOKEN):
    raise SystemExit(
        "TELEGRAM_BOT_TOKEN missing/invalid. Set TELEGRAM_BOT_TOKEN in .env or environment"
    )
if not WEBAPP_URL.startswith("https://"):
    raise SystemExit("WEBAPP_URL must start with https://")
if not BACKEND_ORIGIN.startswith("https://"):
    raise SystemExit("BACKEND_ORIGIN must start with https://")
if not FRONTEND_ORIGIN.startswith("https://"):
    raise SystemExit("FRONTEND_ORIGIN must start with https://")
if not SECRET_KEY:
    raise SystemExit("SECRET_KEY missing. Set it in .env or environment")

# === Security ===
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')


# === Installed apps ===
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sslserver',
    'django.contrib.sites',          # Sites (kerak bo‘lsa)
    'rest_framework',
    'rest_framework_simplejwt',
    'social_django',
    'account',
    'recipes',
    'analytics',
    'auth_telegram',
    'django_filters',         # to‘g‘ri
    'django_extensions',      # to‘g‘ri
]

try:  # pragma: no cover - drf_yasg optional
    import drf_yasg  # type: ignore
except Exception:
    pass
else:
    INSTALLED_APPS.append('drf_yasg')

AUTH_USER_MODEL = 'account.User'
SITE_ID = 1

# === REST framework ===
"""
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'account.authentication.FlexibleJWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/minute',
        'anon': '10/minute',
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}
"""

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'account.authentication.FlexibleJWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '10000/minute',  # juda katta qiymat — test uchun
        'anon': '10000/minute',  # ab testi uchun kerak
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

"""
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=3),    # 5 daqiqa
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=7),  # 10 daqiqa
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
"""
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# === Social Auth (Google) ===
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {'access_type': 'online', 'prompt': 'select_account'}
SOCIAL_AUTH_LOGIN_REDIRECT_URL = 'http://localhost:3000'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/swagger/'
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'account.pipeline.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# === Middleware ===
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

# === URL configuration ===
ROOT_URLCONF = 'Mazzaly_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'Mazzaly_backend.wsgi.application'

# === Database (SQLite) ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# === Static and Media ===
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Path to GeoIP database for country lookup
GEOIP_PATH = BASE_DIR / 'geoip'

# .gitignore faylida **media/** ni qo‘shing!

# === Default primary key field type ===
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# === Swagger (drf-yasg) ===
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'DEFAULT_INFO': 'Mazzaly_backend.urls.schema_view',
}
# === Internationalization ===
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# === Email Configuration ===
# Default to console backend for development. If EMAIL_HOST_USER and
# EMAIL_HOST_PASSWORD are provided, use SMTP settings for sending real
# emails (e.g. via Gmail).

#EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
#EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

#if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
 #   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
 #   EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
 #   EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
 #   EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
 #   DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
#else:
 #   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)




SPOONACULAR_API_KEY = config('SPOONACULAR_API_KEY', default='')
EDAMAM_APP_ID = config('EDAMAM_APP_ID', default='')
EDAMAM_APP_KEY = config('EDAMAM_APP_KEY', default='')
EDAMAM_USER_ID = config('EDAMAM_USER_ID', default='')
EDAMAM_ACCOUNT_USER = config('EDAMAM_ACCOUNT_USER', default=EDAMAM_USER_ID)

# CORS settings
# Allow specifying additional origins via the CORS_ALLOWED_ORIGINS env var.
# Comma separated values are supported, e.g. "http://localhost:8080,https://mazzaly.uz".
cors_origins = config('CORS_ALLOWED_ORIGINS', default=BACKEND_ORIGIN)
CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins.split(',') if o.strip()]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# === HTTPS / Security Settings ===
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)

