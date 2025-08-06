import os
import json
from dotenv import load_dotenv

load_dotenv()

try:  # pragma: no cover - optional dependency
    import openai
    try:
        from openai import OpenAI  # type: ignore
    except Exception:  # pragma: no cover - v0 API
        OpenAI = None  # type: ignore
except Exception:  # pragma: no cover - library may be missing
    openai = None  # type: ignore
    OpenAI = None  # type: ignore

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


LANGUAGE_NAMES = {'en': 'English', 'uz': 'Uzbek', 'ru': 'Russian'}


def _chatgpt_translate(text: str, dest: str, src: str) -> str:
    """Translate text using OpenAI's ChatGPT API."""
    if not openai:
        print("OpenAI package not installed; cannot translate via ChatGPT")
        return ""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set; cannot translate via ChatGPT")
        return ""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional culinary translator. "
                "Provide natural, context-aware translations and return only the translated text."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Translate this cooking-related text from {LANGUAGE_NAMES.get(src, src)} "
                f"to {LANGUAGE_NAMES.get(dest, dest)}:\n{text}"
            ),
        },
    ]
    try:  # pragma: no cover - network
        if hasattr(openai, "ChatCompletion"):
            # Legacy openai<1.0 client
            openai.api_key = api_key
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0,
            )
            return completion.choices[0].message["content"].strip()
        elif OpenAI:
            # New openai>=1.0 client
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0,
            )
            return completion.choices[0].message.content.strip()
    except Exception as exc:
        # Surface translation failures so they're visible in the management command
        print(f"ChatGPT translation failed: {exc}")
        return ""
    return ""


def generate_description(name: str, category: str, area: str, instructions: str) -> str:
    """Generate a short English description for a recipe using ChatGPT."""
    if not openai:
        return ""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""
    try:  # pragma: no cover - network
        if category or area or instructions:
            prompt_parts = [f"Dish name: {name}."]
            if category:
                prompt_parts.append(f"Category: {category}.")
            if area:
                prompt_parts.append(f"Cuisine: {area}.")
            if instructions:
                prompt_parts.append(
                    "Main steps: " + instructions.strip().replace("\n", " ")[:200]
                )
            prompt = " ".join(prompt_parts)
        else:
            prompt = f"Dish name: {name}."
        messages = [
            {
                "role": "system",
                "content": "You are a professional recipe writer. Write concise, engaging descriptions.",
            },
            {"role": "user", "content": f"Write a 1-2 sentence description of this dish. {prompt}"},
        ]
        if hasattr(openai, "ChatCompletion"):  # openai<1.0
            openai.api_key = api_key
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            return completion.choices[0].message["content"].strip()
        elif OpenAI:  # openai>=1.0
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            return completion.choices[0].message.content.strip()
    except Exception:
        return ""
    return ""


def translate_text(text: str, dest: str, src: str = 'en') -> str:
    """Translate text to the destination language with context-aware wording."""
    if not text:
        return ''
    manual = _manual_translate(text, dest)
    if manual:
        return manual
    result = _chatgpt_translate(text, dest, src)
    return _manual_translate(text, dest) or result or text


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

