"""Service for translating normalized recipe structures to Uzbek and Russian."""

from __future__ import annotations

import logging
from typing import Dict, List

from .translation_google import translate_list, translate_text

logger = logging.getLogger("recipes")


def translate_json(recipe: Dict) -> Dict:
    """Translate all translatable fields in ``recipe``.

    Returns a new dict containing the original data plus translated fields:
    ``name_uz``, ``name_ru``, ``description_uz``, ``description_ru``,
    ``categories_uz``, ``categories_ru``, ``ingredients_uz``, ``ingredients_ru``,
    ``steps_uz`` and ``steps_ru``.
    """
    result = dict(recipe)
    try:
        result["name_uz"] = translate_text(recipe.get("name", ""), "uz")
        result["name_ru"] = translate_text(recipe.get("name", ""), "ru")
        result["description_uz"] = translate_text(recipe.get("description", ""), "uz")
        result["description_ru"] = translate_text(recipe.get("description", ""), "ru")
        categories = recipe.get("categories", [])
        ingredients = recipe.get("ingredients", [])
        steps = recipe.get("steps", [])
        result["categories_uz"] = translate_list(categories, "uz")
        result["categories_ru"] = translate_list(categories, "ru")
        result["ingredients_uz"] = translate_list(ingredients, "uz")
        result["ingredients_ru"] = translate_list(ingredients, "ru")
        result["steps_uz"] = translate_list(steps, "uz")
        result["steps_ru"] = translate_list(steps, "ru")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Translation failed: %s", exc)
    return result
