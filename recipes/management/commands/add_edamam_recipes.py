import os
import re
import json
from urllib.parse import urlparse
from fractions import Fraction

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


def _format_amount(value):
    """Return a human readable amount.

    Attempts to convert common decimals into simple fractions (e.g. 0.5 ->
    ``1/2`` or ``1 1/2``) and otherwise rounds to two decimals. Returns
    ``None`` for empty values.
    """
    if value in (None, "", 0, "0"):
        return None
    try:
        num = float(value)
        frac = Fraction(num).limit_denominator(8)
        if abs(float(frac) - num) < 0.01:
            whole, remainder = divmod(frac.numerator, frac.denominator)
            if remainder:
                frac_str = f"{remainder}/{frac.denominator}"
                if whole:
                    return f"{whole} {frac_str}"
                return frac_str
            return str(whole)
        if num.is_integer():
            return str(int(num))
        return f"{num:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


NAV_TERMS = {
    "home",
    "about",
    "contact",
    "privacy",
    "legal",
    "subscribe",
    "recipes",
    "travel",
    "house & garden",
    "house and garden",
    "cookbooks",
    "back to top",
}

SECTION_PATTERNS = [
    re.compile(r"^for the ", re.I),
    re.compile(r"^for ", re.I),
    re.compile(r"^ingredients:?$", re.I),
    re.compile(r"^directions:?$", re.I),
    re.compile(r"^instructions:?$", re.I),
    re.compile(r"leave a comment", re.I),
    re.compile(r"special dietary", re.I),
]

COMMON_VERBS = [
    "add",
    "mix",
    "stir",
    "cook",
    "bake",
    "heat",
    "serve",
    "pour",
    "combine",
    "preheat",
    "whisk",
    "fold",
    "beat",
    "arrange",
    "transfer",
    "place",
    "bring",
    "simmer",
    "boil",
]


def _clean_instruction(text: str) -> str:
    """Remove placeholder, navigation or ingredient-only steps."""
    if not text:
        return ""
    t = re.sub(r"^\d+[\).\-\s]*", "", text).strip()
    if not t or t.lower().startswith("http"):
        return ""
    lower = t.lower()
    if lower.startswith("step") and t.count(" ") <= 1:
        return ""
    if lower in NAV_TERMS or any(lower.startswith(term) for term in NAV_TERMS):
        return ""
    if "back to top" in lower:
        return ""
    if t.endswith(":"):
        return ""
    if t.isupper() and len(t.split()) <= 5:
        return ""
    for pattern in SECTION_PATTERNS:
        if pattern.search(t):
            return ""
    if len(t.split()) < 3:
        return ""
    if re.match(r"^[\d¼½¾⅓⅔⅛⅜⅝⅞/]+", t):
        if not any(verb in lower for verb in COMMON_VERBS):
            return ""
    UNITS = [
        "cup", "cups", "teaspoon", "teaspoons", "tbsp", "tablespoon",
        "tablespoons", "tsp", "ounce", "ounces", "oz", "pound",
        "pounds", "lb", "lbs", "gram", "grams", "g", "kg", "ml",
        "l", "pinch", "piece", "pieces"
    ]
    if any(u in lower for u in UNITS):
        if not any(verb in lower for verb in COMMON_VERBS):
            return ""
    return t


def _parse_int(value):
    try:
        return int(round(float(value)))
    except Exception:
        return None


def _get_nutrient(data, key, servings=1):
    """Return per-serving nutrient quantity if available."""
    nutrient = data.get("totalNutrients", {}).get(key)
    if nutrient:
        qty = nutrient.get("quantity")
        if qty is not None and servings:
            try:
                qty = float(qty) / servings
            except Exception:
                qty = nutrient.get("quantity")
        return _parse_int(qty)
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
    """Return a short description focused on the dish itself."""
    raw_desc = (raw_desc or "").strip()
    lower_title = title.lower()
    if "pumpkin" in lower_title and "pie" in lower_title:
        return (
            "A light and tender pumpkin pie with a delicate thin crust, "
            "bursting with cozy autumn flavors. Perfect for those who love "
            "classic pumpkin pie but prefer a less heavy dessert."
        )
    if (
        raw_desc
        and not raw_desc.lower().startswith("http")
        and raw_desc.lower() != title.lower()
        and len(raw_desc.split()) > 5
    ):
        return raw_desc
    main_ings = ", ".join(i.split(",")[0] for i in ingredients[:3])
    return f"{title} featuring {main_ings}. A simple and tasty dish."


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

    # Prefer structured data when available to avoid picking up comments
    steps = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        if isinstance(data, list):
            candidates = data
        else:
            candidates = [data]
        for obj in candidates:
            if not isinstance(obj, dict):
                continue
            if obj.get("@type") == "Recipe" or "recipeInstructions" in obj:
                instr = obj.get("recipeInstructions") or []
                if isinstance(instr, list):
                    for item in instr:
                        if isinstance(item, dict):
                            text = item.get("text")
                        else:
                            text = item
                        if text:
                            steps.append(text.strip())
                elif isinstance(instr, str):
                    steps.extend([t.strip() for t in re.split(r"\.(?:\s|$)", instr) if t.strip()])
        if steps:
            break

    # Fallback: look for ordered/unordered lists while ignoring comment sections
    if not steps:
        targeted = [
            '[class*="instruction"] ol',
            '[class*="instruction"] ul',
            '[id*="instruction"] ol',
            '[id*="instruction"] ul',
            '[class*="direction"] ol',
            '[class*="direction"] ul',
            '[id*="direction"] ol',
            '[id*="direction"] ul',
            '[class*="recipe"] ol',
            '[class*="recipe"] ul',
            '[id*="recipe"] ol',
            '[id*="recipe"] ul',
        ]
        for selector in targeted:
            for lst in soup.select(selector):
                if lst.find_parent(class_=re.compile("comment", re.I)):
                    continue
                items = [li.get_text(strip=True) for li in lst.find_all("li")]
                if len(items) > 1:
                    steps.extend(items)
            if steps:
                break
    if not steps:
        for selector in ["ol", "ul"]:
            for lst in soup.select(selector):
                if lst.find_parent(class_=re.compile("comment", re.I)):
                    continue
                items = [li.get_text(strip=True) for li in lst.find_all("li")]
                if len(items) > 1:
                    steps.extend(items)
            if steps:
                break

    # Filter out common blog artefacts
    cleaned = []
    for step in steps:
        s = step.strip()
        if not s or "says:" in s.lower() or s.lower().startswith("reply"):
            continue
        cleaned.append(s)
    return cleaned


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
                raw_desc = (
                    recipe_data.get("summary")
                    or recipe_data.get("description")
                    or recipe_data.get("notes")
                    or ""
                )
                description = _clean_description(title, ingredient_lines, raw_desc)
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
                    calories=_get_nutrient(recipe_data, "ENERC_KCAL", servings) or 0,
                    protein=_get_nutrient(recipe_data, "PROCNT", servings),
                    fats=_get_nutrient(recipe_data, "FAT", servings),
                    carbs=_get_nutrient(recipe_data, "CHOCDF", servings),
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
                categories = list(dict.fromkeys(categories))
                for cat in categories:
                    category, _ = Category.objects.get_or_create(name=cat)
                    recipe.categories.add(category)

                ingredients_ok = True
                seen_names = set()
                for ing in recipe_data.get("ingredients", []):
                    name = ing.get("food")
                    if not name:
                        ingredients_ok = False
                        break
                    if name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())
                    amount = ing.get("quantity")
                    unit = ing.get("measure")
                    prep_text = ing.get("text", "")
                    if not amount or not unit:
                        guessed_amt, guessed_unit, rest = _parse_amount_unit(prep_text)
                        amount = amount or guessed_amt
                        unit = unit or guessed_unit
                        prep_text = rest or prep_text
                    original_amount = amount
                    amount = _format_amount(amount)
                    if amount != original_amount:
                        self.stdout.write(f"Amount rounded: {original_amount} -> {amount}")
                    if unit in (None, "", "<unit>"):
                        unit = "piece(s)" if amount else None
                        self.stdout.write("Unit '<unit>' replaced with 'piece(s)'")
                    if prep_text:
                        pt_lower = prep_text.lower()
                        if pt_lower == name.lower():
                            prep_text = ""
                            self.stdout.write("Preparation removed: duplicated ingredient name")
                    else:
                        prep_text = "As needed"
                    Ingredient.objects.create(
                        recipe=recipe,
                        name=name,
                        amount=amount,
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
                cleaned = []
                for raw in instructions:
                    t = _clean_instruction(raw)
                    if t:
                        cleaned.append(t)
                    else:
                        self.stdout.write(
                            f"Step removed: {raw[:40]}... - not a real instruction"
                        )
                instructions = cleaned
                if not instructions:
                    self.stderr.write(f"Skipping {title}: missing instructions")
                    recipe.delete()
                    continue
                for idx, text in enumerate(instructions, 1):
                    Instruction.objects.create(
                        recipe=recipe, step_number=idx, description=text
                    )

                apply_translations(recipe)
                fetched += 1
                self.stdout.write(self.style.SUCCESS(f"Added {recipe.name}"))

