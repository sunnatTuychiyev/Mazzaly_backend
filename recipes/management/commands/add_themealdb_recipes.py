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
            type=str,
            help="Search term used to query TheMealDB API",
        )

    def handle(self, search_term, *args, **options):
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={search_term}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # pragma: no cover - network errors
            self.stderr.write(f"Error fetching data: {exc}")
            return

        meals = data.get("meals")
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

            recipe = Recipe.objects.create(
                name=name,
                description=meal.get("strInstructions") or "",
                prep_time=10,
                cook_time=10,
                servings=1,
                subscription_plan=Recipe.PLAN_STANDARD,
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
            for cat in categories:
                category, _ = Category.objects.get_or_create(name=cat)
                recipe.categories.add(category)

            for i in range(1, 21):
                ing_name = meal.get(f"strIngredient{i}")
                if ing_name and ing_name.strip():
                    measure = meal.get(f"strMeasure{i}")
                    Ingredient.objects.create(
                        recipe=recipe,
                        name=ing_name.strip(),
                        amount=measure.strip() if measure and measure.strip() else None,
                    )

            instructions = meal.get("strInstructions")
            if instructions:
                steps = [s.strip() for s in instructions.splitlines() if s.strip()]
                for num, step in enumerate(steps, start=1):
                    Instruction.objects.create(
                        recipe=recipe,
                        step_number=num,
                        description=step,
                    )

            apply_translations(recipe)
            self.stdout.write(self.style.SUCCESS(f"Added {recipe.name}"))
