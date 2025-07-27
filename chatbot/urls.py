from django.urls import path
from .views import ChatMessageView, ChatImageView

urlpatterns = [
    path('chatbot/message/', ChatMessageView.as_view(), name='chatbot-message'),
    path('chatbot/image/', ChatImageView.as_view(), name='chatbot-image'),
]
