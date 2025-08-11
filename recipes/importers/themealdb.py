from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List

import requests

from .base import BaseImporter
from recipes.utils.sanitization import clean_text, ensure_list


class TheMealDBImporter(BaseImporter):
    source = "themealdb"

    def fetch(self, category: str, max: int | None = None, **kwargs) -> Iterable[Dict[str, Any]]:
        base = os.getenv("THEMEALDB_BASE_URL", "https://www.themealdb.com/api/json/v1/1")
        resp = requests.get(f"{base}/filter.php", params={"c": category}, timeout=10)
        resp.raise_for_status()
        meals = resp.json().get("meals", [])
        ids = [m["idMeal"] for m in meals]
        if max:
            ids = ids[:max]
        for meal_id in ids:
            r = requests.get(f"{base}/lookup.php", params={"i": meal_id}, timeout=10)
            r.raise_for_status()
            data = r.json().get("meals")
            if data:
                yield data[0]

    def normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        ingredients: List[str] = []
        for i in range(1, 21):
            name = clean_text(item.get(f"strIngredient{i}"))
            measure = clean_text(item.get(f"strMeasure{i}"))
            if name:
                ingredients.append(f"{measure} {name}".strip())
        steps = [clean_text(s) for s in item.get("strInstructions", "").split("\n") if clean_text(s)]
        return {
            "source_id": item.get("idMeal"),
            "name": clean_text(item.get("strMeal")),
            "description": clean_text(item.get("strArea", "")),
            "categories": ensure_list(item.get("strCategory")),
            "ingredients": ingredients,
            "steps": steps,
            "image_url": item.get("strMealThumb"),
        }
