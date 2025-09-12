from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.generic import TemplateView

from account.telegram import get_user_from_init_data, TelegramInitDataError
import json

from .models import RecipeSubmission, RecipeSubmissionImage, Category
from .serializers import RecipeSubmissionSerializer, CategorySerializer


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

        # ``request.data`` is a ``QueryDict`` when using ``MultiPartParser``.
        # Calling ``dict()`` or ``pop()`` on it would coerce multi-value fields
        # like ``categories`` into scalars and also includes uploaded files such
        # as ``images``.  Iterate over ``lists()`` instead so we can decide which
        # keys should remain lists and skip file fields that are handled
        # separately below.
        data = {}
        for key, values in request.data.lists():
            if key in {"init_data", "images"}:
                continue
            data[key] = values if key == "categories" else values[0]

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


class TelegramCategoryCreateView(APIView):
    """Create a new category directly from a Telegram WebApp."""

    def post(self, request):
        init_data = request.data.get('init_data')
        if not init_data:
            return Response({'error': 'init_data is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            get_user_from_init_data(init_data)
        except TelegramInitDataError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'name_uz': request.data.get('name_uz'),
            'name_ru': request.data.get('name_ru'),
        }
        serializer = CategorySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class TelegramCategoryFormView(TemplateView):
    template_name = "telegram/category_form.html"
