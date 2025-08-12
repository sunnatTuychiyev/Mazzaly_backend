from __future__ import annotations

import os
from typing import Any, Dict, Iterable

import requests

from .base import BaseImporter
from recipes.utils.sanitization import clean_text, ensure_list


class EdamamImporter(BaseImporter):
    source = "edamam"

    def fetch(self, query: str, max: int = 50, **kwargs) -> Iterable[Dict[str, Any]]:
        app_id = os.getenv("EDAMAM_APP_ID")
        app_key = os.getenv("EDAMAM_APP_KEY")
        url = "https://api.edamam.com/api/recipes/v2"
        fetched = 0
        while fetched < max:
            params = {
                "type": "public",
                "q": query,
                "app_id": app_id,
                "app_key": app_key,
                "from": fetched,
                "to": min(fetched + 20, max),
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("hits", [])
            if not hits:
                break
            for hit in hits:
                yield hit.get("recipe", {})
                fetched += 1
                if fetched >= max:
                    break

    def normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        categories = ensure_list(item.get("cuisineType", [])) + ensure_list(item.get("mealType", []))
        ingredients = [clean_text(i) for i in item.get("ingredientLines", [])]
        steps = ensure_list(item.get("instructions", [])) or ensure_list(item.get("instructionLines", []))
        return {
            "source_id": item.get("uri", ""),
            "name": clean_text(item.get("label")),
            "description": clean_text(item.get("source", "")),
            "categories": categories,
            "ingredients": ingredients,
            "steps": steps,
            "image_url": item.get("image"),
        }
