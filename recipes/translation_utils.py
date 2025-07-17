from typing import Dict, List

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

try:
    from googletrans import Translator  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Translator = None  # type: ignore

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
