import re
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from .serializers import (
    ChatMessageSerializer,
    ChatResponseSerializer,
    ImageUploadSerializer,
    ImageResponseSerializer,
)
from recipes.models import Recipe


HF_TEXT_MODEL = 'microsoft/DialoGPT-medium'
HF_IMAGE_MODEL = 'microsoft/vision-calorie-estimator'
HF_API_URL = 'https://api-inference.huggingface.co/models/'


def query_huggingface(model: str, payload, is_json=True):
    url = HF_API_URL + model
    headers = {}
    token = getattr(settings, 'HUGGINGFACE_API_TOKEN', '')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        if is_json:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
        else:
            resp = requests.post(url, headers=headers, files=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def generate_text_response(text: str) -> str:
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    data = query_huggingface(HF_TEXT_MODEL, payload)
    if isinstance(data, list) and data:
        generated = data[0].get('generated_text')
    elif isinstance(data, dict):
        generated = data.get('generated_text')
    else:
        generated = None
    return generated or "I'm not sure how to answer that."


def handle_recipe_query(message: str) -> str | None:
    lower = message.lower()
    if 'what can i make with' in lower or 'what can i cook with' in lower:
        parts = re.split(r'with', lower, maxsplit=1)
        if len(parts) > 1:
            ingredients_str = parts[1]
            ing_names = [i.strip() for i in re.split(',|and', ingredients_str) if i.strip()]
            qs = Recipe.objects.all()
            for ing in ing_names:
                qs = qs.filter(ingredients__name__icontains=ing)
            recipes = list(qs.distinct().values_list('name', flat=True)[:5])
            if recipes:
                return 'You can cook: ' + ', '.join(recipes)
            return 'No recipes found with those ingredients.'
    if 'how do i cook' in lower or 'how to cook' in lower:
        name = re.split(r'cook', lower, maxsplit=1)[1].strip().rstrip('?')
        recipe = Recipe.objects.filter(name__icontains=name).first()
        if recipe:
            steps = recipe.instructions.order_by('step_number').values_list('description', flat=True)
            text = 'Steps to cook {}: '.format(recipe.name)
            text += ' '.join(f"{i+1}. {s}" for i, s in enumerate(steps))
            return text
        return 'Recipe not found.'
    if 'kcal' in lower or 'calorie' in lower:
        words = lower.replace('?', '').split()
        for i, w in enumerate(words):
            if w in {'kcal', 'calorie', 'calories'} and i >= 1:
                name = ' '.join(words[i+1:]) or words[i-1]
                break
        else:
            name = lower
        recipe = Recipe.objects.filter(name__icontains=name).first()
        if recipe and recipe.calories:
            return f"{recipe.name} has approximately {recipe.calories} kcal per serving."
        if recipe:
            return f"Calorie information for {recipe.name} is not available."
    if 'vegetarian' in lower:
        recipes = Recipe.objects.filter(categories__name__icontains='vegetarian').values_list('name', flat=True)[:5]
        if recipes:
            return 'Vegetarian options: ' + ', '.join(recipes)
    if 'high protein' in lower or 'protein' in lower:
        recipes = Recipe.objects.filter(protein__gte=20).order_by('-protein').values_list('name', flat=True)[:5]
        if recipes:
            return 'High protein dishes: ' + ', '.join(recipes)
    if 'healthy' in lower:
        recipes = Recipe.objects.filter(healthy=True).values_list('name', flat=True)[:5]
        if recipes:
            return 'Healthy choices: ' + ', '.join(recipes)
    return None


class ChatbotMessageView(APIView):
    """Handle text messages for the chatbot."""

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data['message']
        reply = handle_recipe_query(message)
        if not reply:
            reply = generate_text_response(message)
        return Response({'response': reply}, status=status.HTTP_200_OK)


class ChatbotImageView(APIView):
    """Handle food image uploads."""

    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.validated_data['image']
        files = {'file': image.read()}
        data = query_huggingface(HF_IMAGE_MODEL, files, is_json=False)
        food = None
        calories = None
        if isinstance(data, dict):
            food = data.get('food_name') or data.get('label')
            calories = data.get('calories') or data.get('kcal')
        if not food:
            food = 'Unknown'
        if calories is None:
            calories = 0.0
        return Response({'food_name': food, 'calories': calories}, status=status.HTTP_200_OK)

