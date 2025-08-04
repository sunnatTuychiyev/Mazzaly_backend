from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.conf import settings
from recipes.models import Recipe, Ingredient, Instruction, Category
from recipes.translation_utils import apply_translations
import os
import json
import requests
from urllib.parse import urlparse
import re


def _parse_amount(value):
    """Return an integer from a numeric value or string with units."""
    if value is None or value == "":
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        if isinstance(value, str):
            match = re.search(r"([-\d\.]+)", value)
            if match:
                try:
                    return int(round(float(match.group(1))))
                except ValueError:
                    return None
    return None


def _get_nutrient(recipe_data, *names):
    """Return a nutrient value from the Spoonacular nutrition block."""
    nutrients = recipe_data.get("nutrition", {}).get("nutrients") or []
    lowered = [n.lower() for n in names]
    for nutrient in nutrients:
        name = nutrient.get("name", "").lower()
        if name in lowered:
            return _parse_amount(nutrient.get("amount"))
    return None


def _short_description(text, max_len=200):
    """Return a plain short description with HTML stripped."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip()
    if len(text) > max_len:
        end = text.find(".", 0, max_len)
        if end != -1:
            text = text[: end + 1]
        else:
            text = text[: max_len].rsplit(" ", 1)[0] + "..."
    return text


def _download_image(path, base_dir=None):
    """Download an image from a URL or load it from a local path."""
    if not path:
        return None, None

    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        try:
            resp = requests.get(path, timeout=10)
            resp.raise_for_status()
        except Exception:
            return None, None
        filename = os.path.basename(parsed.path) or "image.jpg"
        return filename, ContentFile(resp.content)

    # Local file path
    file_path = path
    if base_dir and not os.path.isabs(file_path):
        file_path = os.path.join(base_dir, file_path)
    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except Exception:
        return None, None
    filename = os.path.basename(file_path)
    return filename, ContentFile(data)

class Command(BaseCommand):
    help = "Fetch recipes from Spoonacular API and populate the database"

    def add_arguments(self, parser):
        parser.add_argument('--number', type=int, default=5,
                            help='Number of recipes to fetch from the API')
        parser.add_argument('--file', type=str, help='Path to a local JSON file with Spoonacular format data')
        parser.add_argument(
            '--tags',
            type=str,
            default=None,
            help="Comma-separated tags to filter recipe types",
        )
        parser.add_argument(
            '--meal-type',
            choices=['breakfast', 'lunch', 'dinner', 'random'],
            dest='meal_type',
            help='Meal type to filter recipes',
        )

    def handle(self, *args, **options):
        base_dir = None
        if options.get('file'):
            self.stdout.write(f"Loading recipes from {options['file']}")
            with open(options['file'], 'r') as f:
                data = json.load(f)
            base_dir = os.path.dirname(options['file']) or None
        else:
            api_key = os.getenv('SPOONACULAR_API_KEY') or getattr(settings, 'SPOONACULAR_API_KEY', None)
            if not api_key:
                raise CommandError('SPOONACULAR_API_KEY not set')
            url = 'https://api.spoonacular.com/recipes/random'
            params = {
                'apiKey': api_key,
                'number': options['number'],
                'addRecipeInformation': True,
                'addRecipeNutrition': True,
            }
            tags = options.get('tags')
            meal_type = options.get('meal_type')
            if meal_type == 'random':
                meal_type = None
            if meal_type and tags:
                params['tags'] = f"{tags},{meal_type}"
            elif meal_type:
                params['tags'] = meal_type
            elif tags:
                params['tags'] = tags
            self.stdout.write('Fetching recipes from Spoonacular...')
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        recipes = data.get('recipes', [])
        if not recipes:
            self.stdout.write(self.style.WARNING('No recipes found in provided data'))
            return
        for r in recipes:
            calories = _get_nutrient(r, 'Calories', 'Energy', 'Energy (kcal)')
            if not calories:
                self.stderr.write(
                    f"Skipping {r.get('title', 'No title')}: missing calorie info"
                )
                continue

            recipe = Recipe.objects.create(
                name=r.get('title', 'No title'),
                description=_short_description(r.get('summary')),
                prep_time=r.get('readyInMinutes') or 0,
                cook_time=r.get('readyInMinutes') or 0,
                servings=r.get('servings', 1),
                healthy=r.get('veryHealthy', False),
                subscription_plan=(
                    Recipe.PLAN_HEALTHY if r.get('veryHealthy', False) else Recipe.PLAN_STANDARD
                ),
                calories=calories,
                protein=_get_nutrient(r, 'Protein', 'Proteins'),
                fats=_get_nutrient(r, 'Fat', 'Fats', 'Total Fat'),
                carbs=_get_nutrient(r, 'Carbohydrates', 'Carbs', 'Carbohydrate'),
            )
            filename, content = _download_image(r.get('image'), base_dir=base_dir)
            if content:
                recipe.image.save(filename, content, save=True)
            elif r.get('image'):
                self.stderr.write(f"Could not download image for {r.get('title')}")
            for cat in r.get('dishTypes', []) + r.get('diets', []):
                category, _ = Category.objects.get_or_create(name=cat)
                recipe.categories.add(category)
            for ing in r.get('extendedIngredients', []):
                Ingredient.objects.create(
                    recipe=recipe,
                    name=ing.get('name', ''),
                    amount=str(ing.get('amount', '')),
                    unit=ing.get('unit', ''),
                )
            instructions = r.get('analyzedInstructions') or []
            if instructions:
                for inst in instructions:
                    for step in inst.get('steps', []):
                        Instruction.objects.create(
                            recipe=recipe,
                            step_number=step.get('number', 1),
                            description=step.get('step', ''),
                        )
            else:
                raw_instructions = r.get('instructions', '')
                parts = [p.strip() for p in re.split(r"[\n\.]", raw_instructions) if p.strip()]
                for num, desc in enumerate(parts, 1):
                    Instruction.objects.create(
                        recipe=recipe,
                        step_number=num,
                        description=desc,
                    )
            apply_translations(recipe)
            self.stdout.write(self.style.SUCCESS(f'Added {recipe.name}'))
