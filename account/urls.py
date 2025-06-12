from django.urls import path
from .views import RegisterView, LoginView, ProfileView, GoogleAuthView, VerifyEmailView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
]
