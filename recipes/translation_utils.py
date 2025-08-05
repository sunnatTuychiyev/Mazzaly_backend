import os

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



def _libre_translate(text: str, dest: str, src: str) -> str:
    """Translate text using the public LibreTranslate API."""
    try:  # pragma: no cover - network
        data = {"q": text, "source": src, "target": dest, "format": "text"}
        api_key = os.getenv("LIBRETRANSLATE_API_KEY")
        if api_key:
            data["api_key"] = api_key
        resp = requests.post("https://libretranslate.com/translate", data=data, timeout=10)
        resp.raise_for_status()
        return resp.json().get("translatedText", "")
    except Exception:
        return ""




def translate_text(text: str, dest: str, src: str = 'en') -> str:
    """Translate text to the destination language using LibreTranslate."""
    if not text or dest == src:
        return text

    result = _libre_translate(text, dest, src)
    return result or text


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
