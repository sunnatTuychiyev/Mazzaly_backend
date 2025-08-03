import os
from urllib.parse import urlparse

import requests
try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv():
        pass
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Category, Ingredient, Instruction, Recipe
from recipes.translation_utils import apply_translations


BANNED_INGREDIENTS = [
    "pork",
    "ham",
    "bacon",
    "lard",
    "beer",
    "wine",
    "rum",
    "vodka",
    "whiskey",
    "whisky",
    "cognac",
    "brandy",
    "alcohol",
]


def _parse_int(value):
    try:
        return int(round(float(value)))
    except Exception:
        return None


def _get_nutrient(data, key):
    nutrient = data.get("totalNutrients", {}).get(key)
    if nutrient:
        return _parse_int(nutrient.get("quantity"))
    return None


def _is_halal(text: str) -> bool:
    lowered = text.lower()
    return not any(bad in lowered for bad in BANNED_INGREDIENTS)


class Command(BaseCommand):
    help = "Fetch halal recipes from Edamam API and populate the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "count",
            type=int,
            help="Number of recipes to fetch from the API",
        )
        parser.add_argument(
            "--query",
            default="egg",
            help="Ingredient or dish to search for (default: egg)",
        )

    def handle(self, *args, **options):
        load_dotenv()

        app_id = os.getenv("EDAMAM_APP_ID") or getattr(
            settings, "EDAMAM_APP_ID", None
        )
        app_key = os.getenv("EDAMAM_APP_KEY") or getattr(
            settings, "EDAMAM_APP_KEY", None
        )
        account_user = (
            os.getenv("EDAMAM_ACCOUNT_USER")
            or os.getenv("EDAMAM_USER_ID")
            or getattr(settings, "EDAMAM_ACCOUNT_USER", None)
            or getattr(settings, "EDAMAM_USER_ID", None)
        )
        if not app_id or not app_key or not account_user:
            raise CommandError(
                "EDAMAM_APP_ID, EDAMAM_APP_KEY and EDAMAM_ACCOUNT_USER must be set"
            )

        to_fetch = options["count"]
        query = options["query"]
        fetched = 0
        while fetched < to_fetch:
            params = {
                "type": "public",
                "q": query,
                "app_id": app_id,
                "app_key": app_key,
                "random": "true",
                "health": ["pork-free", "alcohol-free"],
            }
            try:
                resp = requests.get(
                    "https://api.edamam.com/api/recipes/v2",
                    params=params,
                    headers={"Edamam-Account-User": account_user},
                    timeout=10,
                )
            except requests.exceptions.RequestException as exc:
                self.stderr.write(f"API request failed: {exc}")
                return

            if resp.status_code != 200:
                self.stderr.write(f"HTTP Status: {resp.status_code}")
                self.stderr.write(f"Response: {resp.text}")
                if resp.status_code in (401, 403):
                    raise CommandError(
                        f"Edamam API request unauthorized: {resp.status_code} {resp.text}. "
                        "Check EDAMAM_APP_ID, EDAMAM_APP_KEY and EDAMAM_ACCOUNT_USER"
                    )
                raise CommandError(
                    f"Edamam API request failed: {resp.status_code} {resp.text}"
                )

            hits = resp.json().get("hits", [])
            if not hits:
                self.stdout.write(self.style.WARNING("No recipes found"))
                return

            for hit in hits:
                if fetched >= to_fetch:
                    break
                recipe_data = hit.get("recipe", {})
                ingredient_lines = recipe_data.get("ingredientLines") or []
                if any(not _is_halal(line) for line in ingredient_lines):
                    continue

                recipe = Recipe.objects.create(
                    name=recipe_data.get("label", "No title"),
                    description=recipe_data.get("source", ""),
                    prep_time=_parse_int(recipe_data.get("totalTime")) or 0,
                    cook_time=0,
                    servings=_parse_int(recipe_data.get("yield")) or 1,
                    subscription_plan=
                        Recipe.PLAN_HEALTHY
                        if "Low-Fat" in recipe_data.get("healthLabels", [])
                        else Recipe.PLAN_STANDARD,
                    calories=_get_nutrient(recipe_data, "ENERC_KCAL"),
                    protein=_get_nutrient(recipe_data, "PROCNT"),
                    fats=_get_nutrient(recipe_data, "FAT"),
                    carbs=_get_nutrient(recipe_data, "CHOCDF"),
                )

                image_url = recipe_data.get("image")
                if image_url:
                    try:
                        img_resp = requests.get(image_url, timeout=10)
                        img_resp.raise_for_status()
                        filename = os.path.basename(urlparse(image_url).path) or "image.jpg"
                        recipe.image.save(filename, ContentFile(img_resp.content), save=True)
                    except Exception:
                        self.stderr.write(
                            f"Could not download image for {recipe_data.get('label')}"
                        )

                categories = (
                    recipe_data.get("cuisineType", [])
                    + recipe_data.get("mealType", [])
                    + recipe_data.get("dishType", [])
                )
                for cat in categories:
                    category, _ = Category.objects.get_or_create(name=cat)
                    recipe.categories.add(category)

                for ing in recipe_data.get("ingredients", []):
                    Ingredient.objects.create(
                        recipe=recipe,
                        name=ing.get("food", ""),
                        amount=str(ing.get("quantity") or ""),
                        unit=ing.get("measure") or "",
                        preparation=ing.get("text", ""),
                    )

                instructions = recipe_data.get("instructionLines") or []
                if not instructions:
                    url = recipe_data.get("url")
                    if url:
                        instructions = [f"See the original recipe: {url}"]
                for idx, text in enumerate(instructions, 1):
                    Instruction.objects.create(
                        recipe=recipe, step_number=idx, description=text
                    )

                apply_translations(recipe)
                fetched += 1
                self.stdout.write(self.style.SUCCESS(f"Added {recipe.name}"))

