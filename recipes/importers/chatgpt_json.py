from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from .base import BaseImporter
from recipes.utils.sanitization import clean_text, ensure_list


class ChatGPTJSONImporter(BaseImporter):
    source = "chatgpt"

    def fetch(self, file: str, max: int | None = None, **kwargs) -> Iterable[Dict[str, Any]]:
        data = json.loads(Path(file).read_text(encoding="utf-8"))
        recipes = data if isinstance(data, list) else data.get("recipes", [])
        if max:
            recipes = recipes[:max]
        for r in recipes:
            yield r

    def normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source_id": str(item.get("id", item.get("name"))),
            "name": clean_text(item.get("name")),
            "description": clean_text(item.get("description", "")),
            "categories": ensure_list(item.get("categories")),
            "ingredients": ensure_list(item.get("ingredients")),
            "steps": ensure_list(item.get("steps")),
            "image_url": item.get("image_url"),
        }
