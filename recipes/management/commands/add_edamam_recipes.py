import os
import re
from urllib.parse import urlparse

import requests
try:  # pragma: no cover - optional dependency
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None
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


def _parse_amount_unit(text: str):
    """Guess amount and unit from a free-form ingredient line."""
    if not text:
        return None, None, ""
    match = re.match(r"(?P<amount>[\d/.,]+)?\s*(?P<unit>[a-zA-Z]+)?\s*(?P<rest>.*)", text)
    if match:
        amount = match.group("amount") or None
        unit = match.group("unit") or None
        rest = match.group("rest").strip()
        return amount, unit, rest
    return None, None, text


def _clean_description(title, ingredients, raw_desc):
    """Return a non-empty description summarising the recipe."""
    raw_desc = (raw_desc or "").strip()
    if (
        raw_desc
        and not raw_desc.lower().startswith("http")
        and raw_desc.lower() != title.lower()
        and len(raw_desc.split()) > 3
    ):
        return raw_desc
    main_ings = ", ".join(i.split(",")[0] for i in ingredients[:3])
    return f"{title} made with {main_ings}."


def _estimate_times(title):
    """Estimate preparation and cook times when missing."""
    lowered = title.lower()
    if "salad" in lowered:
        return 10, 0
    if "omelet" in lowered or "omelette" in lowered:
        return 5, 5
    if any(w in lowered for w in ["bake", "cake", "bread", "roast"]):
        return 15, 45
    return 15, 15


def _guess_categories(title, ingredient_lines):
    guessed = []
    lowered = title.lower()
    if "salad" in lowered:
        guessed.append("Salad")
    if "soup" in lowered:
        guessed.append("Soup")
    if any("chicken" in line.lower() for line in ingredient_lines):
        guessed.append("Chicken")
    return guessed


def _fetch_instructions(url):
    """Try to scrape instructions from the recipe page."""
    if not url or not BeautifulSoup:
        return []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    steps = []
    # Look for ordered/unordered lists
    for selector in ["ol", "ul"]:
        for lst in soup.select(selector):
            items = [li.get_text(strip=True) for li in lst.find_all("li")]
            if len(items) > 1:
                steps.extend(items)
        if steps:
            break
    return steps


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

                title = recipe_data.get("label", "No title")
                description = _clean_description(title, ingredient_lines, recipe_data.get("source", ""))
                prep = _parse_int(recipe_data.get("totalTime"))
                cook = 0
                if not prep or prep == 0:
                    prep, cook = _estimate_times(title)
                servings = _parse_int(recipe_data.get("yield")) or 2

                image_url = recipe_data.get("image")
                if not image_url or "127.0.0.1" in image_url or "localhost" in image_url:
                    image_url = None
                if not image_url:
                    self.stderr.write(f"Skipping {title}: no valid image")
                    continue

                # verify image is downloadable
                try:
                    img_resp = requests.get(image_url, timeout=10)
                    img_resp.raise_for_status()
                except Exception:
                    self.stderr.write(f"Skipping {title}: unable to download image")
                    continue

                recipe = Recipe.objects.create(
                    name=title,
                    description=description,
                    prep_time=prep,
                    cook_time=cook,
                    servings=servings,
                    subscription_plan=
                        Recipe.PLAN_HEALTHY
                        if "Low-Fat" in recipe_data.get("healthLabels", [])
                        else Recipe.PLAN_STANDARD,
                    calories=_get_nutrient(recipe_data, "ENERC_KCAL"),
                    protein=_get_nutrient(recipe_data, "PROCNT"),
                    fats=_get_nutrient(recipe_data, "FAT"),
                    carbs=_get_nutrient(recipe_data, "CHOCDF"),
                )

                filename = os.path.basename(urlparse(image_url).path) or "image.jpg"
                recipe.image.save(filename, ContentFile(img_resp.content), save=True)

                categories = (
                    recipe_data.get("cuisineType", [])
                    + recipe_data.get("mealType", [])
                    + recipe_data.get("dishType", [])
                )
                if not categories:
                    categories = _guess_categories(title, ingredient_lines)
                for cat in categories:
                    category, _ = Category.objects.get_or_create(name=cat)
                    recipe.categories.add(category)

                ingredients_ok = True
                for ing in recipe_data.get("ingredients", []):
                    amount = ing.get("quantity")
                    unit = ing.get("measure")
                    prep_text = ing.get("text", "")
                    if not amount or not unit:
                        guessed_amt, guessed_unit, rest = _parse_amount_unit(prep_text)
                        amount = amount or guessed_amt
                        unit = unit or guessed_unit
                        prep_text = rest or prep_text
                    if not prep_text:
                        prep_text = "As needed"
                    if not ing.get("food"):
                        ingredients_ok = False
                        break
                    Ingredient.objects.create(
                        recipe=recipe,
                        name=ing.get("food"),
                        amount=str(amount) if amount else None,
                        unit=unit,
                        preparation=prep_text,
                    )
                if not ingredients_ok:
                    self.stderr.write(f"Skipping {title}: incomplete ingredient data")
                    recipe.delete()
                    continue

                instructions = recipe_data.get("instructionLines") or []
                if instructions and len(instructions) == 1:
                    if "See the original recipe" in instructions[0]:
                        instructions = []
                    else:
                        parts = re.split(r"\.(?:\s|$)", instructions[0].strip())
                        instructions = [p.strip() for p in parts if p.strip()]
                if not instructions:
                    instructions = _fetch_instructions(recipe_data.get("url"))
                if not instructions:
                    self.stderr.write(f"Skipping {title}: missing instructions")
                    recipe.delete()
                    continue
                for idx, text in enumerate(instructions, 1):
                    if not text.strip():
                        continue
                    Instruction.objects.create(
                        recipe=recipe, step_number=idx, description=text.strip()
                    )

                apply_translations(recipe)
                fetched += 1
                self.stdout.write(self.style.SUCCESS(f"Added {recipe.name}"))

