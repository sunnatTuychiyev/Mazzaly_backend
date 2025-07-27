from django.urls import path
from .views import ChatbotMessageView, ChatbotImageView

urlpatterns = [
    path('message/', ChatbotMessageView.as_view(), name='chatbot-message'),
    path('image/', ChatbotImageView.as_view(), name='chatbot-image'),
]
