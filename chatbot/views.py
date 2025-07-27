import re
import requests
from django.conf import settings
from django.db.models import Q
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
    """Send a request to a Hugging Face model with optional auth."""

    url = HF_API_URL + model
    token = getattr(settings, "HUGGINGFACE_API_TOKEN", None)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        if is_json:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
        else:
            resp = requests.post(url, headers=headers, files=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # If something went wrong (e.g. network issues or invalid token),
        # return ``None`` so the caller can handle the fallback response.
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
    """Return a reply using known recipes if the question is food related."""

    text = message.lower().strip()

    # What can I make with chicken and rice?
    m = re.search(r"what can i (?:make|cook) with (.+)", text)
    if m:
        ingredients = m.group(1)
        ing_names = [i.strip() for i in re.split(r",|and", ingredients) if i.strip()]
        qs = Recipe.objects.all()
        for ing in ing_names:
            qs = qs.filter(
                Q(ingredients__name__icontains=ing)
                | Q(ingredients__name_ru__icontains=ing)
                | Q(ingredients__name_uz__icontains=ing)
            )
        recipes = list(qs.distinct().values_list("name", flat=True)[:5])
        if recipes:
            return "You can cook: " + ", ".join(recipes)
        return "No recipes found with those ingredients."

    # How do I cook plov?
    m = re.search(r"(?:how do i|how to) cook ([\w\s-]+)", text)
    if m:
        name = m.group(1).strip()
        recipe = Recipe.objects.filter(
            Q(name__icontains=name)
            | Q(name_ru__icontains=name)
            | Q(name_uz__icontains=name)
        ).first()
        if recipe:
            steps = recipe.instructions.order_by("step_number").values_list("description", flat=True)
            return "Steps to cook {}: {}".format(
                recipe.name,
                " ".join(f"{i+1}. {s}" for i, s in enumerate(steps)),
            )
        return "Recipe not found."

    # Ingredients for <dish>
    m = re.search(r"ingredients (?:for|of) ([\w\s-]+)", text)
    if m:
        name = m.group(1).strip()
        recipe = Recipe.objects.filter(
            Q(name__icontains=name)
            | Q(name_ru__icontains=name)
            | Q(name_uz__icontains=name)
        ).first()
        if recipe:
            ingr = recipe.ingredients.values_list("name", flat=True)
            return f"Ingredients for {recipe.name}: " + ", ".join(ingr)
        return "Recipe not found."

    # Calorie questions
    if any(word in text for word in {"kcal", "calories", "calorie"}):
        # try to extract recipe name after the keyword
        m = re.search(r"(?:kcal|calories?|calorie)(?: does)? ([\w\s-]+) have", text)
        if not m:
            m = re.search(r"(?:kcal|calories?|calorie) in ([\w\s-]+)", text)
        if m:
            name = m.group(1).strip()
        else:
            # fallback: last word(s)
            parts = re.split(r"kcal|calories?|calorie", text, maxsplit=1)
            name = parts[1].strip() if len(parts) > 1 else text
        recipe = Recipe.objects.filter(
            Q(name__icontains=name)
            | Q(name_ru__icontains=name)
            | Q(name_uz__icontains=name)
        ).first()
        if recipe and recipe.calories:
            return f"{recipe.name} has approximately {recipe.calories} kcal per serving."
        if recipe:
            return f"Calorie information for {recipe.name} is not available."

    # Healthy/vegetarian/protein suggestions
    if "vegetarian" in text:
        recipes = Recipe.objects.filter(
            Q(categories__name__icontains="vegetarian")
            | Q(categories__name_ru__icontains="vegetarian")
            | Q(categories__name_uz__icontains="vegetarian")
        ).values_list("name", flat=True)[:5]
        if recipes:
            return "Vegetarian options: " + ", ".join(recipes)
    if "healthy" in text:
        recipes = Recipe.objects.filter(healthy=True).values_list("name", flat=True)[:5]
        if recipes:
            return "Healthy recipes: " + ", ".join(recipes)
    if "high protein" in text or ("protein" in text and "high" in text):
        recipes = (
            Recipe.objects.filter(protein__gte=20)
            .order_by("-protein")
            .values_list("name", flat=True)[:5]
        )
        if recipes:
            return "High protein dishes: " + ", ".join(recipes)

    # Description of a recipe
    m = re.search(r"(?:describe|tell me about|what is|explain) ([\w\s-]+)", text)
    if m:
        name = m.group(1).strip()
        recipe = Recipe.objects.filter(
            Q(name__icontains=name)
            | Q(name_ru__icontains=name)
            | Q(name_uz__icontains=name)
        ).first()
        if recipe:
            return f"{recipe.name}: {recipe.description}"
        return "Recipe not found."

    return None


class ChatbotMessageView(APIView):
    """Handle text messages for the chatbot."""

    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]
        reply = handle_recipe_query(message)
        if not reply:
            reply = generate_text_response(message)
        return Response({"response": reply}, status=status.HTTP_200_OK)


class ChatbotImageView(APIView):
    """Handle food image uploads."""

    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.validated_data["image"]
        image.seek(0)
        files = {"file": (image.name, image.read())}
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

