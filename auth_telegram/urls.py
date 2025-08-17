from django.urls import path
from .views import TelegramLoginView, MeView

urlpatterns = [
    path('auth/telegram/login/', TelegramLoginView.as_view(), name='telegram-login'),
    path('me/', MeView.as_view(), name='me'),
]
