from django.urls import path
from .views import TelegramLoginView, MeView, AuthorPickerView

urlpatterns = [
    path('auth/telegram/login/', TelegramLoginView.as_view(), name='telegram-login'),
    path('me/', MeView.as_view(), name='me'),
    path('mini/author-picker/', AuthorPickerView.as_view(), name='author-picker'),
]
