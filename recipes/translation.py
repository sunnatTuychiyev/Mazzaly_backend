from typing import Dict, List

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
    """Translate a single piece of text."""
    if not text:
        return ''
    if _TRANSLATOR:
        try:
            return _TRANSLATOR.translate(text, src=src, dest=dest).text
        except Exception:  # pragma: no cover - optional dependency
            pass
    return _manual_translate(text, dest)


def translate_texts(texts: List[str], dest: str, src: str = 'en') -> List[str]:
    """Translate a list of strings in bulk."""
    cleaned = [t for t in texts if t]
    if not cleaned:
        return []
    if _TRANSLATOR:
        try:
            translations = _TRANSLATOR.translate(cleaned, src=src, dest=dest)
            if isinstance(translations, list):
                return [t.text for t in translations]
            return [translations.text]
        except Exception:  # pragma: no cover - optional dependency
            pass
    return [_manual_translate(t, dest) for t in cleaned]


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
