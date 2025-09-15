from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from account.models import User
from .utils import verify_init_data, TelegramInitDataError


class MiniAppIndexView(TemplateView):
    template_name = 'miniapp/index.html'


class AuthorPickerView(TemplateView):
    template_name = 'miniapp/author_picker.html'


@method_decorator(csrf_exempt, name='dispatch')
class TelegramLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        init_data = request.data.get('init_data', '')
        try:
            res = verify_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
        except TelegramInitDataError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        user_data = res.get('user') or {}
        telegram_id = str(user_data.get('id')) if user_data else None
        if not telegram_id:
            return Response({'detail': 'Invalid user data'}, status=status.HTTP_400_BAD_REQUEST)
        user, _ = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'email': f'tg_{telegram_id}@example.com',
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'is_email_verified': True,
            },
        )
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({'access': access, 'user': {
            'id': user.id,
            'telegram_id': user.telegram_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }})
        response.set_cookie(
            'access', access, httponly=True, secure=True,
            samesite='None', path='/', max_age=3600
        )
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'telegram_id': user.telegram_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
