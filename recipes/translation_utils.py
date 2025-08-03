import os
from typing import Dict, List

try:
    from googletrans import Translator
except Exception:  # pragma: no cover - library may be missing
    Translator = None

try:  # pragma: no cover - optional dependency
    import openai
except Exception:  # pragma: no cover
    openai = None

# Supported languages for translations and API responses
SUPPORTED_LANGUAGES = ['en', 'uz', 'ru']

def get_requested_lang(request) -> str:
    """Return a supported language code from the request query params."""
    if not request:
        return 'en'
    lang = request.query_params.get('lang', 'en')
    if lang not in SUPPORTED_LANGUAGES:
        return 'en'
    return lang


FALLBACK_DICT: Dict[str, Dict[str, str]] = {
    'uz': {
        'chicken': 'tovuq',
        'onion': 'piyoz',
        'salt': 'tuz',
        'pepper': 'qalampir',
        'water': 'suv',
        'dinner': 'kechki ovqat',
        'breakfast': 'nonushta',
        'lunch': 'tushlik',
        'italian': 'italyan',
        'condiment': "qo'shimcha",
        'dip': 'dip',
        'spread': 'surma',
        'soup': "sho'rva",
        'gluten': 'glyuten',
        'free': 'siz',
        'ketogenic': 'ketogen',
        'starter': 'aperitif',
        'appetizer': 'ishtaha ochuvchi',
        'dessert': 'shirinlik',
        'snack': 'tamaddi',
        'main': 'asosiy',
        'course': 'taom',
        'antipasti': 'antipasti',
        'hor': 'hor',
        "d'oeuvre": 'doeuvre',
    },
    'ru': {
        'chicken': 'курица',
        'onion': 'лук',
        'salt': 'соль',
        'pepper': 'перец',
        'water': 'вода',
        'dinner': 'ужин',
        'breakfast': 'завтрак',
        'lunch': 'обед',
        'italian': 'итальянский',
        'condiment': 'приправа',
        'dip': 'соус',
        'spread': 'намазка',
        'soup': 'суп',
        'gluten': 'глютен',
        'free': 'свободный',
        'ketogenic': 'кетогенный',
        'starter': 'закуска',
        'appetizer': 'закуска',
        'dessert': 'десерт',
        'snack': 'перекус',
        'main': 'основное',
        'course': 'блюдо',
        'antipasti': 'антипасти',
        'hor': 'гор',
        "d'oeuvre": 'девр',
    },
}

# Additional phrase-level translations for better accuracy
PHRASE_DICT: Dict[str, Dict[str, str]] = {
    'ru': {
        "gluten free": 'без глютена',
        "main course": 'основное блюдо',
        "hor d'oeuvre": 'закуска',
    },
    'uz': {
        "gluten free": 'glyutensiz',
        "main course": 'asosiy taom',
        "hor d'oeuvre": 'aperitif',
    },
}


def _openai_translate(text: str, dest: str, src: str) -> str:
    """Translate using OpenAI if available and configured."""
    if not openai or not os.getenv("OPENAI_API_KEY"):
        return ""
    try:  # pragma: no cover - network
        openai.api_key = os.getenv("OPENAI_API_KEY")
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Translate from {src} to {dest}."},
                {"role": "user", "content": text},
            ],
            max_tokens=60,
        )
        return resp.choices[0].message["content"].strip()
    except Exception:
        return ""


def _manual_translate(text: str, dest: str) -> str:
    """Simple phrase and word based translation."""
    mapping = FALLBACK_DICT.get(dest, {})
    phrases = PHRASE_DICT.get(dest, {})
    lowered = text.lower()
    if lowered in phrases:
        return phrases[lowered]
    words = text.split()
    translated: List[str] = [mapping.get(word.lower(), word) for word in words]
    return ' '.join(translated)

# Instantiate translator with a short timeout so network issues fail fast
try:  # pragma: no cover - network usage not exercised in tests
    _translator = Translator(timeout=5) if Translator else None
except Exception:  # If initialization fails, fall back to manual dictionary
    _translator = None


def translate_text(text: str, dest: str, src: str = 'en') -> str:
    """Translate text to the destination language.

    Tries OpenAI's API first when configured, then googletrans, and finally
    a small built-in dictionary as a last resort.
    """
    if not text:
        return ''
    global _translator
    result = _openai_translate(text, dest, src)
    if result:
        return result
    if _translator:
        try:
            return _translator.translate(text, src=src, dest=dest).text
        except Exception:
            _translator = None  # Disable translator after first failure
    return _manual_translate(text, dest)


def apply_translations(recipe):
    """Populate translation fields for a recipe, its ingredients and instructions."""
    languages = ['uz', 'ru']
    for lang in languages:
        setattr(recipe, f'name_{lang}', translate_text(recipe.name, lang))
        setattr(recipe, f'description_{lang}', translate_text(recipe.description, lang))
    recipe.save()

    for category in recipe.categories.all():
        for lang in languages:
            setattr(category, f'name_{lang}', translate_text(category.name, lang))
        category.save()

    for ingredient in recipe.ingredients.all():
        for lang in languages:
            setattr(ingredient, f'name_{lang}', translate_text(ingredient.name, lang))
        ingredient.save()

    for step in recipe.instructions.all():
        for lang in languages:
            setattr(step, f'description_{lang}', translate_text(step.description, lang))
        step.save()
