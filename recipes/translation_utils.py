from typing import Dict, List

import requests

# Translators from third party packages are intentionally not used so that
# LibreTranslate becomes the single external service for translations.

# Supported languages for translations and API responses
SUPPORTED_LANGUAGES = ['en', 'uz', 'ru']

LANG_NAMES = {
    'en': 'English',
    'uz': 'Uzbek',
    'ru': 'Russian',
}

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


def _libre_translate(text: str, dest: str, src: str) -> str:
    """Translate text using the public LibreTranslate API."""
    try:  # pragma: no cover - network
        resp = requests.post(
            "https://libretranslate.com/translate",
            data={"q": text, "source": src, "target": dest, "format": "text"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("translatedText", "")
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




def translate_text(text: str, dest: str, src: str = 'en') -> str:
    """Translate text to the destination language.

    Uses the LibreTranslate API first and falls back to a small built-in
    dictionary only if the API doesn't return a translation.
    """
    if not text:
        return ''

    result = _libre_translate(text, dest, src)
    if result and result.lower() != text.lower():
        return result

    # Fallback to manual dictionary only for short phrases
    if len(text.split()) <= 3:
        manual = _manual_translate(text, dest)
        if manual.lower() != text.lower():
            return manual

    return text


def apply_translations(recipe):
    """Populate translation fields for a recipe, its ingredients and instructions."""
    languages = ['uz', 'ru']
    for lang in languages:
        name_trans = translate_text(recipe.name, lang)
        desc_trans = translate_text(recipe.description, lang)
        setattr(recipe, f'name_{lang}', name_trans or recipe.name)
        setattr(recipe, f'description_{lang}', desc_trans or recipe.description)
    recipe.save()

    for category in recipe.categories.all():
        for lang in languages:
            trans = translate_text(category.name, lang)
            setattr(category, f'name_{lang}', trans or category.name)
        category.save()

    for ingredient in recipe.ingredients.all():
        for lang in languages:
            trans = translate_text(ingredient.name, lang)
            setattr(ingredient, f'name_{lang}', trans or ingredient.name)
        ingredient.save()

    steps = list(recipe.instructions.order_by('step_number'))
    for lang in languages:
        joined = "\n".join(step.description for step in steps)
        translated_block = translate_text(joined, lang)
        if translated_block and translated_block.count("\n") == len(steps) - 1:
            lines = translated_block.split("\n")
        else:
            lines = [translate_text(step.description, lang) for step in steps]
        for step, line in zip(steps, lines):
            setattr(step, f'description_{lang}', line or step.description)
    for step in steps:
        step.save()
