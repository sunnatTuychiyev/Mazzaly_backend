from django.urls import path
from .views import RegisterView, LoginView, ProfileView, GoogleAuthView, VerifyEmailView, TelegramAuthView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    path('telegram-auth/', TelegramAuthView.as_view(), name='telegram-auth'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
]
