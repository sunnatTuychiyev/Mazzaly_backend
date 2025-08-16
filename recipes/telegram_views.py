from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.generic import TemplateView

from account.telegram import get_user_from_init_data, TelegramInitDataError
from .models import RecipeSubmission, RecipeSubmissionImage
from .serializers import RecipeSubmissionSerializer


class TelegramRecipeSubmissionCreateView(APIView):
    """Create a new recipe submission from a Telegram WebApp."""
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        init_data = request.data.get('init_data')
        if not init_data:
            return Response({'error': 'init_data is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = get_user_from_init_data(init_data)
        except TelegramInitDataError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data.pop('init_data', None)
        serializer = RecipeSubmissionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        submission = RecipeSubmission.objects.create(user=user, **serializer.validated_data)

        images = request.FILES.getlist('images')
        if len(images) > 5:
            return Response({'error': 'Maximum 5 images allowed'}, status=status.HTTP_400_BAD_REQUEST)
        for img in images:
            RecipeSubmissionImage.objects.create(submission=submission, image=img)

        return Response(RecipeSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class TelegramRecipeSubmissionMineView(APIView):
    """List submissions created by the Telegram user."""

    def get(self, request):
        init_data = request.query_params.get('init_data')
        if not init_data:
            return Response({'error': 'init_data is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = get_user_from_init_data(init_data)
        except TelegramInitDataError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        submissions = RecipeSubmission.objects.filter(user=user).order_by('-created_at')
        serializer = RecipeSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class TelegramRecipeFormView(TemplateView):
    template_name = 'telegram/recipe_form.html'
