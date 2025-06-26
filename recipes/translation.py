from typing import Dict, List

try:
    from googletrans import Translator  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Translator = None  # type: ignore

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
    """Translate text using googletrans if available, otherwise a small fallback."""
    if not text:
        return ''
    if Translator:
        try:
            translator = Translator()
            return translator.translate(text, src=src, dest=dest).text
        except Exception:
            pass
    return _manual_translate(text, dest)


def translate_recipe(recipe) -> Dict[str, Dict[str, str]]:
    """Return a dictionary with Uzbek and Russian translations of recipe fields."""
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
            'uz': [translate_text(i.name, 'uz') for i in recipe.ingredients.all()],
            'ru': [translate_text(i.name, 'ru') for i in recipe.ingredients.all()],
        },
        'instructions': {
            'uz': [translate_text(step.description, 'uz') for step in recipe.instructions.all()],
            'ru': [translate_text(step.description, 'ru') for step in recipe.instructions.all()],
        },
    }
    return data
