from typing import Dict, List

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


def apply_translations(recipe):
    """Populate translation fields for a recipe, its ingredients and instructions."""
    languages = ['uz', 'ru']
    for lang in languages:
        setattr(recipe, f'name_{lang}', translate_text(recipe.name, lang))
        setattr(recipe, f'description_{lang}', translate_text(recipe.description, lang))
    recipe.save()

    for ingredient in recipe.ingredients.all():
        for lang in languages:
            setattr(ingredient, f'name_{lang}', translate_text(ingredient.name, lang))
        ingredient.save()

    for step in recipe.instructions.all():
        for lang in languages:
            setattr(step, f'description_{lang}', translate_text(step.description, lang))
        step.save()
