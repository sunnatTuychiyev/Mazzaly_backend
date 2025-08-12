from __future__ import annotations

import os
from typing import Any, Dict, Iterable

import requests

from .base import BaseImporter
from recipes.utils.sanitization import clean_text, ensure_list


class SpoonacularImporter(BaseImporter):
    source = "spoonacular"

    def fetch(self, query: str, max: int = 50, **kwargs) -> Iterable[Dict[str, Any]]:
        api_key = os.getenv("SPOONACULAR_API_KEY")
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "query": query,
            "number": max,
            "addRecipeInformation": True,
            "apiKey": api_key,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])

    def normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        ingredients = [clean_text(i.get("original")) for i in item.get("extendedIngredients", [])]
        steps = []
        instructions = item.get("analyzedInstructions", [])
        if instructions:
            for step in instructions[0].get("steps", []):
                steps.append(clean_text(step.get("step")))
        categories = ensure_list(item.get("dishTypes", [])) + ensure_list(item.get("cuisines", []))
        return {
            "source_id": str(item.get("id")),
            "name": clean_text(item.get("title")),
            "description": clean_text(item.get("summary", "")),
            "categories": categories,
            "ingredients": ingredients,
            "steps": steps,
            "image_url": item.get("image"),
        }
