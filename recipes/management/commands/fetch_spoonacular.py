from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.conf import settings
from recipes.models import Recipe, Ingredient, Instruction, Category
import os
import json
import requests
from urllib.parse import urlparse
import re


def _get_nutrient(recipe_data, *names):
    """Return a nutrient value from the Spoonacular nutrition block."""
    nutrients = recipe_data.get("nutrition", {}).get("nutrients") or []
    lowered = [n.lower() for n in names]
    for nutrient in nutrients:
        name = nutrient.get("name", "").lower()
        if name in lowered:
            try:
                return int(round(float(nutrient.get("amount", 0))))
            except (TypeError, ValueError):
                return None
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


def _download_image(url):
    """Download an image from a URL and return a filename and ContentFile."""
    if not url:
        return None, None
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None, None
    filename = os.path.basename(urlparse(url).path) or "image.jpg"
    return filename, ContentFile(resp.content)

class Command(BaseCommand):
    help = "Fetch recipes from Spoonacular API and populate the database"

    def add_arguments(self, parser):
        parser.add_argument('--number', type=int, default=5,
                            help='Number of recipes to fetch from the API')
        parser.add_argument('--file', type=str, help='Path to a local JSON file with Spoonacular format data')

    def handle(self, *args, **options):
        if options.get('file'):
            self.stdout.write(f"Loading recipes from {options['file']}")
            with open(options['file'], 'r') as f:
                data = json.load(f)
        else:
            api_key = os.getenv('SPOONACULAR_API_KEY') or getattr(settings, 'SPOONACULAR_API_KEY', None)
            if not api_key:
                raise CommandError('SPOONACULAR_API_KEY not set')
            url = 'https://api.spoonacular.com/recipes/random'
            params = {'apiKey': api_key, 'number': options['number']}
            self.stdout.write('Fetching recipes from Spoonacular...')
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        recipes = data.get('recipes', [])
        if not recipes:
            self.stdout.write(self.style.WARNING('No recipes found in provided data'))
            return
        for r in recipes:
            recipe = Recipe.objects.create(
                name=r.get('title', 'No title'),
                description=_short_description(r.get('summary')), 
                prep_time=r.get('readyInMinutes') or 0,
                cook_time=r.get('readyInMinutes') or 0,
                servings=r.get('servings', 1),
                healthy=r.get('veryHealthy', False),
                calories=_get_nutrient(r, 'Calories', 'Energy', 'Energy (kcal)'),
                protein=_get_nutrient(r, 'Protein', 'Proteins'),
                fats=_get_nutrient(r, 'Fat', 'Fats', 'Total Fat'),
                carbs=_get_nutrient(r, 'Carbohydrates', 'Carbs', 'Carbohydrate'),
            )
            filename, content = _download_image(r.get('image'))
            if content:
                recipe.image.save(filename, content, save=True)
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
            self.stdout.write(self.style.SUCCESS(f'Added {recipe.name}'))
