from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    GoogleAuthView,
    VerifyEmailView,
    TelegramAuthView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    AuthorViewSet,
    AdminUserViewSet,
    TelegramLinkTokenView,
    TelegramLinkConfirmView,
    EmailOTPSendView,
    EmailOTPVerifyView,
)
from .miniapp_views import MiniAppConnectEmailView, MiniAppVerifyOTPView
from .telegram_link_views import TelegramLinkCreateView, TelegramWebhookView

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'users', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),  # Original endpoint (backward compatible)
    path('telegram-auth/', TelegramAuthView.as_view(), name='telegram-auth'),
    # New Telegram linking endpoints
    path('telegram/link-token/', TelegramLinkTokenView.as_view(), name='telegram-link-token'),
    path('telegram/link/confirm/', TelegramLinkConfirmView.as_view(), name='telegram-link-confirm'),
    # New email verification for Telegram linking
    path('verify-email/send/', EmailOTPSendView.as_view(), name='verify-email-send'),
    path('verify-email/telegram/', EmailOTPVerifyView.as_view(), name='verify-email-telegram'),
    # Mini App email connection endpoints
    path('mini-app/auth/connect-email/', MiniAppConnectEmailView.as_view(), name='miniapp-connect-email'),
    path('mini-app/auth/OTP/', MiniAppVerifyOTPView.as_view(), name='miniapp-verify-otp'),
    # Telegram linking endpoints (web to telegram bot)
    path('mini-app/auth/connect-telegram/link/', TelegramLinkCreateView.as_view(), name='telegram-link-create'),
    path('mini-app/auth/telegram-webhook/', TelegramWebhookView.as_view(), name='telegram-webhook'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
