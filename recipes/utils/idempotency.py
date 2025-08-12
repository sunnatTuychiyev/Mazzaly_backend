from __future__ import annotations
from typing import Tuple

from recipes.models import Recipe


def get_or_create_recipe(source: str, source_id: str, name: str) -> Tuple[Recipe, bool]:
    """Return existing recipe for ``source`` and ``source_id`` or a new unsaved instance.

    The combination of ``source`` and ``source_id`` must be unique. If a recipe is
    found, it is returned with ``created`` set to ``False``. Otherwise a new
    ``Recipe`` instance is created (but not saved) and ``created`` is ``True``.
    """
    recipe = Recipe.objects.filter(source=source, source_id=source_id).first()
    if recipe:
        return recipe, False
    return Recipe(source=source, source_id=source_id, name=name), True
