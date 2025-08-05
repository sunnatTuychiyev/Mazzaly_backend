import re
import requests
from urllib.parse import urlparse

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from recipes.models import Category, Ingredient, Instruction, Recipe
from recipes.translation_utils import apply_translations


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

    def handle(self, search_term="", *args, **options):
        count = options.get("count")
        tags = options.get("tags")
        meal_type = options.get("meal_type")
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
            meals = [m for m in meals if m.get("strCategory", "").lower() == meal_type.lower()]
        tag_list = []
        if tags:
            tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
            meals = [
                m
                for m in meals
                if m.get("strTags") and any(t in m["strTags"].lower() for t in tag_list)
            ]
        if count:
            meals = meals[:count]
        if not meals:
            self.stdout.write(self.style.WARNING("No recipes found."))
            return

        for meal in meals:
            name = meal.get("strMeal")
            if not name:
                continue
            if Recipe.objects.filter(name=name).exists():
                self.stdout.write(f"Skipping existing recipe: {name}")
                continue

            desc_parts = []
            category = meal.get("strCategory")
            if category:
                desc_parts.append(f"This is a {category.lower()} dish.")
            area = meal.get("strArea")
            if area:
                desc_parts.append(f"It originates from {area}.")

            # TheMealDB does not provide a dedicated description field.
            # Use the first sentence from the instructions as a brief summary
            # of the meal so that the description contains short information
            # about the dish.
            instructions_text = meal.get("strInstructions", "")
            if instructions_text:
                first_sentence = instructions_text.strip().split(".")[0].strip()
                if first_sentence:
                    desc_parts.append(f"{first_sentence}.")

            ingredients = []
            for i in range(1, 21):
                ing_name = meal.get(f"strIngredient{i}")
                if ing_name and ing_name.strip():
                    measure = meal.get(f"strMeasure{i}")
                    ingredients.append(
                        (ing_name.strip(), measure.strip() if measure and measure.strip() else None)
                    )

            calories = max(len(ingredients) * 50, 50)
            # Estimate macronutrients using simple proportions of calories.
            protein = round(calories * 0.3 / 4)  # 30% of calories from protein
            fats = round(calories * 0.3 / 9)     # 30% of calories from fats
            carbs = round(calories * 0.4 / 4)    # 40% of calories from carbs

            recipe = Recipe.objects.create(
                name=name,
                description=" ".join(desc_parts),
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
                category, _ = Category.objects.get_or_create(name=cat)
                recipe.categories.add(category)

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
