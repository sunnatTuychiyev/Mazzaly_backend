import json
import os
import re

import openai
import requests
from dotenv import load_dotenv
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Category, Ingredient, Instruction, Recipe


load_dotenv()


FORBIDDEN_INGREDIENTS = {
    "pork",
    "ham",
    "bacon",
    "wine",
    "beer",
    "vodka",
    "whiskey",
    "rum",
    "gin",
    "brandy",
}


def _fetch_google_image(query: str):
    """Fetch first image from Google Images for the given query."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    params = {"q": query, "tbm": "isch"}
    try:
        res = requests.get(
            "https://www.google.com/search", params=params, headers=headers, timeout=10
        )
        res.raise_for_status()
        match = re.search(r'"ou":"(.*?)"', res.text)
        if not match:
            return None, None
        img_url = match.group(1)
        img_res = requests.get(img_url, headers=headers, timeout=10)
        img_res.raise_for_status()
        filename = os.path.basename(img_url.split("?")[0]) or "image.jpg"
        return filename, ContentFile(img_res.content)
    except Exception:
        return None, None


class Command(BaseCommand):
    help = "Generate recipes using ChatGPT and import them into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--search-term",
            dest="search_term",
            default="",
            help="Search term for ChatGPT. Leave blank for random",
        )
        parser.add_argument("--count", type=int, default=1)
        parser.add_argument(
            "--tags",
            type=str,
            default="",
            help="Comma separated tags like 'vegetarian,dessert'",
        )
        parser.add_argument(
            "--meal-type",
            choices=["breakfast", "lunch", "dinner", "random"],
            dest="meal_type",
            default="random",
        )

    def handle(self, *args, **options):
        api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
        if not api_key:
            raise CommandError("OPENAI_API_KEY not set")
        openai.api_key = api_key

        search_term = options.get("search_term") or ""
        count = options.get("count", 1)
        tags = options.get("tags") or ""
        meal_type = options.get("meal_type")
        if meal_type == "random":
            meal_prompt = ""
        else:
            meal_prompt = meal_type

        prompt_parts = [
            f"Generate {count} {meal_prompt} recipes",
        ]
        if search_term:
            prompt_parts.append(f"that include {search_term}")
        if tags:
            prompt_parts.append(f"with tags {tags}")
        prompt_parts.append(
            "Do not use pork, wine, alcohol or similar ingredients. "
            "Respond in English. Return data as a JSON array where each recipe has the keys: name, description, prep_time, cook_time, servings, ingredients (list of objects with name, amount, unit, preparation), instructions (list of objects with step_number and description)."
        )
        prompt = " ".join(prompt_parts)

        response = openai.ChatCompletion.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response["choices"][0]["message"]["content"]
        try:
            recipes_data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON from ChatGPT: {exc}")

        if not isinstance(recipes_data, list):
            recipes_data = [recipes_data]

        for data in recipes_data:
            ingredients = data.get("ingredients", [])
            if any(
                forb in ing.get("name", "").lower()
                for ing in ingredients
                for forb in FORBIDDEN_INGREDIENTS
            ):
                self.stderr.write(
                    f"Skipping {data.get('name', 'Unnamed')} due to forbidden ingredients"
                )
                continue

            def _to_int(value, default=0):
                if isinstance(value, (int, float)):
                    return int(value)
                match = re.search(r"\d+", str(value))
                return int(match.group()) if match else default

            recipe = Recipe.objects.create(
                name=data.get("name", "Unnamed"),
                description=data.get("description", ""),
                prep_time=_to_int(data.get("prep_time")),
                cook_time=_to_int(data.get("cook_time")),
                servings=_to_int(data.get("servings", 1), default=1),
                subscription_plan=Recipe.PLAN_STANDARD,
                healthy=False,
            )

            filename, image_content = _fetch_google_image(recipe.name)
            if image_content:
                recipe.image.save(filename, image_content, save=True)

            category_names = []
            if meal_type and meal_type != "random":
                category_names.append(meal_type)
            if tags:
                category_names.extend([t.strip() for t in tags.split(",") if t.strip()])
            for cat_name in category_names:
                category, _ = Category.objects.get_or_create(name=cat_name)
                if not category.name_ru or not category.name_uz:
                    category.save()
                recipe.categories.add(category)

            for ing in ingredients:
                Ingredient.objects.create(
                    recipe=recipe,
                    name=ing.get("name", ""),
                    amount=str(ing.get("amount", "")),
                    unit=ing.get("unit"),
                    preparation=ing.get("preparation"),
                )
            for step in data.get("instructions", []):
                Instruction.objects.create(
                    recipe=recipe,
                    step_number=_to_int(step.get("step_number", 1), default=1),
                    description=step.get("description", ""),
                )

            self.stdout.write(self.style.SUCCESS(f"Added {recipe.name}"))
