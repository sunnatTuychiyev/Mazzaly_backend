import logging
from typing import Tuple, List, Optional

import requests
from django.conf import settings
from recipes.models import Recipe

logger = logging.getLogger(__name__)

HF_CHAT_MODEL = 'mistralai/Mixtral-8x7B-Instruct-v0.1'
HF_IMAGE_MODEL = 'nutritools/calorie-estimator'


def hf_generate_reply(message: str) -> str:
    """Send a message to the Hugging Face inference API and return the reply."""
    if not settings.HF_API_KEY:
        logger.warning('HF_API_KEY not configured')
        return 'AI features are disabled.'
    url = f"https://api-inference.huggingface.co/models/{HF_CHAT_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
    payload = {"inputs": message}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        if isinstance(data, list) and data:
            return data[0].get('generated_text', '')
        if isinstance(data, dict) and 'generated_text' in data:
            return data['generated_text']
    except Exception as exc:  # pragma: no cover - network call
        logger.exception('HF text generation failed: %s', exc)
    return 'Sorry, I could not process that right now.'


def hf_analyze_image(file_obj) -> Tuple[str, int]:
    """Predict food name and calories using the Hugging Face API."""
    if not settings.HF_API_KEY:
        logger.warning('HF_API_KEY not configured')
        return 'unknown', 0
    url = f"https://api-inference.huggingface.co/models/{HF_IMAGE_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
    try:
        res = requests.post(url, headers=headers, files={"file": file_obj}, timeout=30)
        res.raise_for_status()
        data = res.json()
        food = data.get('food', data.get('label', ''))
        kcal = int(data.get('calories', 0))
        if not food and isinstance(data, list) and data:
            food = data[0].get('label', '')
        return food or 'unknown', kcal
    except Exception as exc:  # pragma: no cover - network call
        logger.exception('HF image analysis failed: %s', exc)
    return 'unknown', 0


def suggest_recipes_from_message(message: str, limit: int = 5) -> List[int]:
    """Return recipe IDs that contain any words from the message as ingredients."""
    import re

    tokens = re.findall(r"\w+", message.lower())
    qs = Recipe.objects.all()
    matched_ids = set()
    for word in tokens:
        ids = qs.filter(ingredients__name__icontains=word).values_list('id', flat=True)
        matched_ids.update(ids)
        if len(matched_ids) >= limit:
            break
    return list(matched_ids)[:limit]


def find_recipe_in_message(message: str) -> Optional[Recipe]:
    """Return a recipe whose name appears in the message (case-insensitive)."""
    lower = message.lower()
    for recipe in Recipe.objects.all():
        if recipe.name.lower() in lower:
            return recipe
    return None


def format_recipe_instructions(recipe: Recipe) -> str:
    """Return numbered instructions for the recipe."""
    steps = recipe.instructions.order_by('step_number')
    lines = [f"{step.step_number}. {step.description}" for step in steps]
    return "\n".join(lines)
