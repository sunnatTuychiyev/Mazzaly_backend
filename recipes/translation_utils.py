import requests

try:
    from googletrans import Translator
except Exception:  # pragma: no cover - library may be missing
    Translator = None

# Supported languages for translations and API responses
SUPPORTED_LANGUAGES = ['en', 'uz', 'ru']

# Manual overrides for problematic machine translations
FALLBACK_DICT = {
    'uz': {
        "american": "amerikancha",
        "desserts": "shirinliklar",
        "biscuits and cookies": "pechene va kukilar",
        "british": "britancha",
        "main dish": "asosiy taom",
        "cereals": "yormalar",
        "pescatarian": "pesketarian",
        "lacto ovo vegetarian": "lakto-ovo vegetarian",
        "dairy free": "sut mahsulotlarisiz",
        "side dish": "yon taom",
        "paleolithic": "paleolitik",
        "primal": "ibtidoiy",
        "mediterranean": "O'rta yer dengizi",
        "ground cinnamon": "maydalangan dolchin",
        "ground nutmeg": "maydalangan muskat yong'og'i",
        "ground allspice": "maydalangan allspice",
        "ground cloves": "maydalangan chinnigullar",
        "instant coffee": "tez eriydigan qahva",
        "unsalted butter": "tuzlanmagan sariyog'",
        "buttermilk": "ayron",
        "cornmeal": "makkajo'xori uni",
        "cornstarch": "makkajo'xori kraxmali",
        "confectioners sugar": "pudra shakari",
        "peppermint": "yalpiz",
        "food coloring": "ovqat bo'yog'i",
    },
    'ru': {},
}


def get_requested_lang(request) -> str:
    """Return a supported language code from the request query params."""
    if not request:
        return 'en'
    lang = request.query_params.get('lang', 'en')
    return lang if lang in SUPPORTED_LANGUAGES else 'en'


def _manual_translate(text: str, dest: str) -> str:
    """Return a manual translation override if one exists."""
    return FALLBACK_DICT.get(dest, {}).get(text.lower(), "")


def _direct_google_translate(text: str, dest: str, src: str) -> str:
    """Fallback to Google Translate's unofficial API via HTTP request."""
    try:  # pragma: no cover - network
        resp = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": src,
                "tl": dest,
                "dt": "t",
                "q": text,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()[0]
        return "".join(part[0] for part in data if part and part[0])
    except Exception:
        return ""


# Instantiate translator with a short timeout so network issues fail fast
try:  # pragma: no cover - network usage not exercised in tests
    _translator = Translator(timeout=5) if Translator else None
except Exception:
    _translator = None


def translate_text(text: str, dest: str, src: str = 'en') -> str:
    """Translate text to the destination language using Google Translate."""
    if not text:
        return ''
    manual = _manual_translate(text, dest)
    if manual:
        return manual
    if _translator:
        try:  # pragma: no cover - network
            result = _translator.translate(text, src=src, dest=dest).text
            if result:
                return result
        except Exception:
            pass
    result = _direct_google_translate(text, dest, src)
    return result or manual or text


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

