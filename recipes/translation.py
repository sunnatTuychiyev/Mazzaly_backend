from typing import Any, Dict, List, Tuple

from deep_translator import GoogleTranslator


def translate_texts(texts: List[str], target: str) -> List[str]:
    """Translate a list of texts using GoogleTranslator. Return originals on error."""
    if not texts:
        return []
    try:
        translator = GoogleTranslator(source="auto", target=target)
        return translator.translate_batch(texts)
    except Exception:
        return texts


def _apply_translations(obj: Dict[str, Any], paths: List[Tuple], translations: List[str]) -> None:
    for path, text in zip(paths, translations):
        target = obj
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = text


def translate_recipe_data(recipe: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """Translate fields of a serialized recipe dict into the given language."""
    texts: List[str] = []
    paths: List[Tuple] = []

    def add(path: Tuple, text: str | None) -> None:
        if text:
            paths.append(path)
            texts.append(text)

    add(("name",), recipe.get("name"))
    add(("description",), recipe.get("description"))
    for i, cat in enumerate(recipe.get("categories", [])):
        add(("categories", i, "name"), cat.get("name"))
    for i, ing in enumerate(recipe.get("ingredients", [])):
        add(("ingredients", i, "name"), ing.get("name"))
        if ing.get("unit"):
            add(("ingredients", i, "unit"), ing.get("unit"))
        if ing.get("preparation"):
            add(("ingredients", i, "preparation"), ing.get("preparation"))
    for i, step in enumerate(recipe.get("instructions", [])):
        add(("instructions", i, "description"), step.get("description"))

    translations = translate_texts(texts, lang)
    _apply_translations(recipe, paths, translations)
    return recipe


def translate_recipe_list(recipes: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    for recipe in recipes:
        translate_recipe_data(recipe, lang)
    return recipes
