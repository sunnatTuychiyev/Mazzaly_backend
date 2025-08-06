import re
import requests
from urllib.parse import urlparse

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from recipes.models import Category, Ingredient, Instruction, Recipe
from recipes.translation_utils import apply_translations, generate_description

# Common non-halal ingredients. Recipes containing any of these will be skipped
# during import. The list is not exhaustive but covers typical pork and
# alcoholic products found in TheMealDB dataset.
HARAM_INGREDIENTS = {
    "pork",
    "ham",
    "bacon",
    "lard",
    "pancetta",
    "prosciutto",
    "salami",
    "pepperoni",
    "chorizo",
    "wine",
    "beer",
    "ale",
    "rum",
    "whiskey",
    "whisky",
    "bourbon",
    "vodka",
    "gin",
    "brandy",
    "tequila",
    "cognac",
    "champagne",
    "sherry",
    "cider",
    "vermouth",
    "sake",
}


class Command(BaseCommand):
    help = "Fetch recipes from TheMealDB API and save them to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "search_term",
            nargs="?",
            default="",
            help="Search term used to query TheMealDB API",
        )
        parser.add_argument(
            "--count",
            type=int,
            dest="count",
            default=None,
            help="Number of recipes to import",
        )
        parser.add_argument(
            "--tags",
            dest="tags",
            default="",
            help="Comma separated tags like 'vegetarian,dessert'",
        )
        parser.add_argument(
            "--meal-type",
            dest="meal_type",
            default="",
            help="Meal type to filter recipes",
        )

    def _create_recipe(self, meal, tag_list):
        name = meal.get("strMeal")
        if not name:
            return False
        if Recipe.objects.filter(name=name).exists():
            self.stdout.write(f"Skipping existing recipe: {name}")
            return False

        category = meal.get("strCategory")
        area = meal.get("strArea")
        instructions_text = meal.get("strInstructions", "")
        description = generate_description(
            name,
            category or "",
            area or "",
            instructions_text or "",
        )
        if not description:
            desc_parts = []
            if category:
                desc_parts.append(f"This is a {category.lower()} dish.")
            if area:
                desc_parts.append(f"It originates from {area}.")
            if instructions_text:
                first_sentence = instructions_text.strip().split(".")[0].strip()
                if first_sentence:
                    desc_parts.append(f"{first_sentence}.")
            description = " ".join(desc_parts)

        ingredients = []
        for i in range(1, 21):
            ing_name = meal.get(f"strIngredient{i}")
            if ing_name and ing_name.strip():
                measure = meal.get(f"strMeasure{i}")
                ingredients.append(
                    (ing_name.strip(), measure.strip() if measure and measure.strip() else None)
                )

        ingredient_names = [ing.lower() for ing, _ in ingredients]
        if any(haram in ing for ing in ingredient_names for haram in HARAM_INGREDIENTS):
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping recipe with non-halal ingredients: {name}"
                )
            )
            return False

        calories = max(len(ingredients) * 50, 50)
        protein = round(calories * 0.3 / 4)
        fats = round(calories * 0.3 / 9)
        carbs = round(calories * 0.4 / 4)

        recipe = Recipe.objects.create(
            name=name,
            description=description,
            prep_time=10,
            cook_time=10,
            servings=1,
            subscription_plan=Recipe.PLAN_STANDARD,
            calories=calories,
            protein=protein,
            fats=fats,
            carbs=carbs,
        )

        image_url = meal.get("strMealThumb")
        if image_url:
            try:
                img_resp = requests.get(image_url, timeout=10)
                img_resp.raise_for_status()
                filename = urlparse(image_url).path.split("/")[-1] or "image.jpg"
                recipe.image.save(filename, ContentFile(img_resp.content), save=True)
            except Exception:
                self.stderr.write(f"Failed to download image for {name}")

        categories = []
        if meal.get("strCategory"):
            categories.append(meal["strCategory"])
        if meal.get("strArea"):
            categories.append(meal["strArea"])
        if meal.get("strTags"):
            categories.extend(
                [c.strip() for c in meal["strTags"].split(",") if c.strip()]
            )
        if tag_list:
            categories.extend(tag_list)
        for cat in categories:
            category_obj, _ = Category.objects.get_or_create(name=cat)
            recipe.categories.add(category_obj)

        for ing_name, measure in ingredients:
            Ingredient.objects.create(
                recipe=recipe,
                name=ing_name,
                amount=measure,
            )

        instructions = meal.get("strInstructions")
        if instructions:
            steps = [
                re.sub(r"^step\s*\d+\.?\s*", "", s.strip(), flags=re.I)
                for s in instructions.splitlines()
                if s.strip()
            ]
            for num, step in enumerate(steps, start=1):
                Instruction.objects.create(
                    recipe=recipe,
                    step_number=num,
                    description=step,
                )

        apply_translations(recipe)
        self.stdout.write(self.style.SUCCESS(f"Added {recipe.name}"))
        desc_uz = getattr(recipe, "description_uz", recipe.description)
        desc_ru = getattr(recipe, "description_ru", recipe.description)
        self.stdout.write(f"Description (UZ): {desc_uz}")
        self.stdout.write(f"Description (RU): {desc_ru}")
        return True

    def handle(self, search_term="", *args, **options):
        count = options.get("count")
        tags = options.get("tags")
        meal_type = options.get("meal_type")

        if search_term.isdigit() and not count:
            count = int(search_term)
            search_term = ""

        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()] if tags else []

        if search_term:
            url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={search_term}"
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:  # pragma: no cover - network errors
                self.stderr.write(f"Error fetching data: {exc}")
                return

            meals = data.get("meals") or []
            if meal_type and meal_type != "random":
                meals = [
                    m
                    for m in meals
                    if m.get("strCategory", "").lower() == meal_type.lower()
                ]
            if tag_list:
                meals = [
                    m
                    for m in meals
                    if m.get("strTags")
                    and any(t in m["strTags"].lower() for t in tag_list)
                ]
            if count:
                meals = meals[:count]
            if not meals:
                self.stdout.write(self.style.WARNING("No recipes found."))
                return
            for meal in meals:
                self._create_recipe(meal, tag_list)
            return

        target = count or 1
        added = 0
        while added < target:
            try:
                resp = requests.get(
                    "https://www.themealdb.com/api/json/v1/1/random.php", timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:  # pragma: no cover - network errors
                self.stderr.write(f"Error fetching data: {exc}")
                return

            meal = (data.get("meals") or [None])[0]
            if not meal:
                continue
            if meal_type and meal_type != "random" and meal.get("strCategory", "").lower() != meal_type.lower():
                continue
            if tag_list and not (meal.get("strTags") and any(t in meal["strTags"].lower() for t in tag_list)):
                continue
            if self._create_recipe(meal, tag_list):
                added += 1

        if added < target:
            self.stdout.write(
                self.style.WARNING("Could not import the requested number of recipes.")
            )
