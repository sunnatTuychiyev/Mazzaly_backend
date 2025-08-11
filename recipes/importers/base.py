"""Base importer providing normalization and persistence helpers."""

from __future__ import annotations

import logging
from typing import Iterable, List, Dict, Any

from django.db import transaction

from recipes.models import Category, Ingredient, Instruction, Recipe
from recipes.translation_service import translate_json
from recipes.utils.idempotency import get_or_create_recipe
from recipes.utils.sanitization import clean_text, ensure_list

logger = logging.getLogger("recipes")


class BaseImporter:
    """Base class for recipe importers."""

    source: str = ""  # name of the source, e.g. "edamam"

    def __init__(self, update: bool = False):
        self.update = update

    # --- API hooks -----------------------------------------------------
    def fetch(self, **kwargs) -> Iterable[Dict[str, Any]]:  # pragma: no cover - abstract
        raise NotImplementedError

    def normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - abstract
        raise NotImplementedError

    # --- import logic --------------------------------------------------
    def import_one(self, data: Dict[str, Any]) -> Recipe | None:
        """Create or update a recipe from normalized ``data``."""
        name = data.get("name", "")
        steps = data.get("steps", [])
        if not name or not steps:
            logger.warning("Missing required fields for %s", data.get("source_id", "?"))
            return None
        translations = translate_json(data)
        if not translations.get("name_uz") and not translations.get("name_ru"):
            logger.warning("Translation failed: %s", name)
        recipe, created = get_or_create_recipe(self.source, data.get("source_id", ""), name)
        if not created and not self.update:
            logger.info("Skipped duplicate: %s", name)
            return None
        # fill fields
        recipe.name = name
        recipe.description = data.get("description", "")
        recipe.image_url = data.get("image_url")
        recipe.source = self.source
        recipe.source_id = data.get("source_id", "")
        recipe.name_uz = translations.get("name_uz", "")
        recipe.name_ru = translations.get("name_ru", "")
        recipe.description_uz = translations.get("description_uz", "")
        recipe.description_ru = translations.get("description_ru", "")
        # for mandatory fields prep_time, cook_time, servings - set to 0 if not present
        recipe.prep_time = data.get("prep_time", 0)
        recipe.cook_time = data.get("cook_time", 0)
        recipe.servings = data.get("servings", 1)
        with transaction.atomic():
            recipe.save()
            # categories
            recipe.categories.clear()
            cats = data.get("categories", [])
            cats_uz = translations.get("categories_uz", [])
            cats_ru = translations.get("categories_ru", [])
            for c, uz, ru in zip(cats, cats_uz, cats_ru):
                category, _ = Category.objects.get_or_create(name=c)
                if uz:
                    category.name_uz = uz
                if ru:
                    category.name_ru = ru
                category.save()
                recipe.categories.add(category)
            # ingredients
            recipe.ingredients.all().delete()
            ing_names = data.get("ingredients", [])
            ing_uz = translations.get("ingredients_uz", [])
            ing_ru = translations.get("ingredients_ru", [])
            for name, uz, ru in zip(ing_names, ing_uz, ing_ru):
                Ingredient.objects.create(
                    recipe=recipe,
                    name=name,
                    name_uz=uz,
                    name_ru=ru,
                )
            # instructions
            recipe.instructions.all().delete()
            steps = data.get("steps", [])
            steps_uz = translations.get("steps_uz", [])
            steps_ru = translations.get("steps_ru", [])
            for idx, (step, uz, ru) in enumerate(zip(steps, steps_uz, steps_ru), start=1):
                Instruction.objects.create(
                    recipe=recipe,
                    step_number=idx,
                    description=step,
                    description_uz=uz,
                    description_ru=ru,
                )
        logger.info(("Added: %s" if created else "Updated: %s"), name)
        return recipe

    def import_all(self, **kwargs) -> List[Recipe]:
        recipes: List[Recipe] = []
        for item in self.fetch(**kwargs):
            try:
                normalized = self.normalize(item)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Normalization failed: %s", getattr(item, "id", "?"))
                continue
            recipe = self.import_one(normalized)
            if recipe:
                recipes.append(recipe)
        return recipes
