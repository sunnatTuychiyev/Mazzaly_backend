from typing import Any, Dict, List, Tuple

from deep_translator import GoogleTranslator


def translate_texts(texts: List[str], target: str, chunk_size: int = 15) -> List[str]:
    """Translate a list of texts. Falls back to originals on any error."""
    if not texts:
        return []

    results: List[str] = []
    try:
        translator = GoogleTranslator(source="auto", target=target, timeout=5)
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i : i + chunk_size]
            translated = translator.translate_batch(chunk)
            # deep-translator may return a single string for one item
            if isinstance(translated, list):
                results.extend(translated)
            else:  # pragma: no cover - defensive
                results.append(translated)
        return results
    except Exception:
        return texts


def _apply_translations(obj: Dict[str, Any], paths: List[Tuple], translations: List[str]) -> None:
    """Apply translated texts to a dict according to stored paths."""
    for path, text in zip(paths, translations):
        target = obj
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = text


def translate_recipe_data(recipe: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """Translate a single serialized recipe dict into ``lang``."""
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
    """Translate a list of serialized recipes in bulk."""
    all_texts: List[str] = []
    all_paths: List[Tuple[int, Tuple]] = []

    def add(idx: int, path: Tuple, text: str | None) -> None:
        if text:
            all_paths.append((idx, path))
            all_texts.append(text)

    for idx, recipe in enumerate(recipes):
        add(idx, ("name",), recipe.get("name"))
        add(idx, ("description",), recipe.get("description"))
        for i, cat in enumerate(recipe.get("categories", [])):
            add(idx, ("categories", i, "name"), cat.get("name"))
        for i, ing in enumerate(recipe.get("ingredients", [])):
            add(idx, ("ingredients", i, "name"), ing.get("name"))
            if ing.get("unit"):
                add(idx, ("ingredients", i, "unit"), ing.get("unit"))
            if ing.get("preparation"):
                add(idx, ("ingredients", i, "preparation"), ing.get("preparation"))
        for i, step in enumerate(recipe.get("instructions", [])):
            add(idx, ("instructions", i, "description"), step.get("description"))

    translations = translate_texts(all_texts, lang)
    for (idx, path), text in zip(all_paths, translations):
        target = recipes[idx]
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = text
    return recipes

