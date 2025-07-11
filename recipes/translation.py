from typing import Dict, List

try:
    # Prefer the official Google Cloud client if credentials are configured
    from google.cloud import translate_v2 as gtranslate  # type: ignore
    _gclient = gtranslate.Client()
except Exception:  # pragma: no cover - optional dependency
    _gclient = None

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
    """Translate text using Google Cloud if available, otherwise a small fallback."""
    if not text:
        return ''
    if _gclient:
        try:
            result = _gclient.translate(text, target_language=dest, source_language=src)
            return result.get('translatedText', text)
        except Exception:
            pass
    return _manual_translate(text, dest)


def get_recipe_translations(recipe) -> Dict[str, Dict[str, str]]:
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


def translate_recipe_data(data: Dict, lang: str) -> Dict:
    """Translate serialized recipe data in-place for the given language."""
    data['name'] = translate_text(data.get('name', ''), lang)
    data['description'] = translate_text(data.get('description', ''), lang)
    for ing in data.get('ingredients', []):
        ing['name'] = translate_text(ing.get('name', ''), lang)
    for step in data.get('instructions', []):
        step['description'] = translate_text(step.get('description', ''), lang)
    return data
