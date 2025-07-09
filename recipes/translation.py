from typing import Dict, List, Tuple
from collections import OrderedDict

try:
    from googletrans import Translator  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Translator = None  # type: ignore

# Keep a single translator instance if the library is available.
if Translator:  # pragma: no cover - optional dependency
    try:
        _TRANSLATOR = Translator()
    except Exception:  # pragma: no cover - optional dependency
        _TRANSLATOR = None
else:
    _TRANSLATOR = None

# Simple in-memory cache for translations
_CACHE: "OrderedDict[Tuple[str, str, str], str]" = OrderedDict()
_CACHE_SIZE = 1024


def _get_cached(text: str, dest: str, src: str) -> str | None:
    key = (text, src, dest)
    result = _CACHE.get(key)
    if result is not None:
        _CACHE.move_to_end(key)
    return result


def _set_cache(text: str, dest: str, src: str, value: str) -> None:
    key = (text, src, dest)
    _CACHE[key] = value
    _CACHE.move_to_end(key)
    if len(_CACHE) > _CACHE_SIZE:
        _CACHE.popitem(last=False)

# Basic fallback dictionaries for common terms
FALLBACK_DICT: Dict[str, Dict[str, str]] = {
    'uz': {
        'chicken': 'tovuq',
        'onion': 'piyoz',
        'salt': 'tuz',
        'pepper': 'qalampir',
        'water': 'suv',
    },
    'ru': {
        'chicken': 'курица',
        'onion': 'лук',
        'salt': 'соль',
        'pepper': 'перец',
        'water': 'вода',
    },
}


def _manual_translate(text: str, dest: str) -> str:
    words = text.split()
    mapping = FALLBACK_DICT.get(dest, {})
    translated: List[str] = [mapping.get(word.lower(), word) for word in words]
    return ' '.join(translated)



def translate_text(text: str, dest: str, src: str = 'en') -> str:
    """Translate a single piece of text with caching."""
    if not text:
        return ''

    cached = _get_cached(text, dest, src)
    if cached is not None:
        return cached

    if _TRANSLATOR:
        try:
            translated = _TRANSLATOR.translate(text, src=src, dest=dest).text
            _set_cache(text, dest, src, translated)
            return translated
        except Exception:  # pragma: no cover - optional dependency
            pass

    translated = _manual_translate(text, dest)
    _set_cache(text, dest, src, translated)
    return translated


def translate_texts(texts: List[str], dest: str, src: str = 'en') -> List[str]:
    """Translate a list of strings with caching."""
    cleaned = [t for t in texts if t]
    if not cleaned:
        return []

    results: List[str | None] = []
    to_translate: List[str] = []
    indices: List[int] = []

    for idx, text in enumerate(cleaned):
        cached = _get_cached(text, dest, src)
        if cached is not None:
            results.append(cached)
        else:
            results.append(None)
            to_translate.append(text)
            indices.append(idx)

    translated: List[str] = []
    if to_translate:
        if _TRANSLATOR:
            try:
                response = _TRANSLATOR.translate(to_translate, src=src, dest=dest)
                if not isinstance(response, list):
                    response = [response]
                translated = [t.text for t in response]
            except Exception:  # pragma: no cover - optional dependency
                translated = [_manual_translate(t, dest) for t in to_translate]
        else:
            translated = [_manual_translate(t, dest) for t in to_translate]

        for idx, inp, out in zip(indices, to_translate, translated):
            results[idx] = out
            _set_cache(inp, dest, src, out)

    # Fill any None values (shouldn't happen)
    for i, res in enumerate(results):
        if res is None:
            fallback = _manual_translate(cleaned[i], dest)
            results[i] = fallback
            _set_cache(cleaned[i], dest, src, fallback)

    return results


def get_recipe_translations(recipe) -> Dict[str, Dict[str, str]]:
    """Return a dictionary with Uzbek and Russian translations of recipe fields."""
    ingredients = list(recipe.ingredients.all())
    instructions = list(recipe.instructions.all())

    ingredient_names = [i.name for i in ingredients]
    instruction_descriptions = [step.description for step in instructions]

    data = {
        'name': {
            'uz': translate_text(recipe.name, 'uz'),
            'ru': translate_text(recipe.name, 'ru'),
        },
        'description': {
            'uz': translate_text(recipe.description, 'uz'),
            'ru': translate_text(recipe.description, 'ru'),
        },
        'ingredients': {
            'uz': translate_texts(ingredient_names, 'uz'),
            'ru': translate_texts(ingredient_names, 'ru'),
        },
        'instructions': {
            'uz': translate_texts(instruction_descriptions, 'uz'),
            'ru': translate_texts(instruction_descriptions, 'ru'),
        },
    }
    return data
