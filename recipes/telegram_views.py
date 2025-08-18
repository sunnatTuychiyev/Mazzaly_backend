from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.generic import TemplateView

from account.telegram import get_user_from_init_data, TelegramInitDataError
import json

from .models import RecipeSubmission, RecipeSubmissionImage, Category
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

        # Convert incoming data to a standard dict while preserving multi-value
        # fields such as ``categories``. ``request.data`` is a ``QueryDict`` when
        # using ``MultiPartParser`` and calling ``.pop()`` on it would return a
        # list which breaks ``json.loads``. ``lists()`` gives us all values for a
        # key so we can keep multi-value items as lists and single values as
        # scalars.
        data = {
            key: values if len(values) > 1 else values[0]
            for key, values in request.data.lists()
        }
        data.pop("init_data", None)

        for src, dest in [
            ("ingredients", "ingredients"),
            ("instructions", "instructions"),
            ("steps", "instructions"),
        ]:
            if src in data and isinstance(data[src], str):
                try:
                    value = data.pop(src)
                    data[dest] = json.loads(value)
                except json.JSONDecodeError:
                    return Response({"error": f"Invalid {src}"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RecipeSubmissionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(user=user)

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
    template_name = "telegram/recipe_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["plans"] = RecipeSubmission.PLAN_CHOICES
        return context
