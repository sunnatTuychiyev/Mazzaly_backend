import os
import json
from typing import Optional
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
    'ru': {
        "american": "американский",
        "desserts": "десерты",
        "biscuits and cookies": "бисквиты и печенье",
        "british": "британский",
        "main dish": "основное блюдо",
        "cereals": "крупы",
        "pescatarian": "пескетарианский",
        "lacto ovo vegetarian": "лакто-ово вегетарианский",
        "dairy free": "без молочных продуктов",
        "side dish": "гарнир",
        "paleolithic": "палеолитический",
        "primal": "первобытный",
        "mediterranean": "средиземноморский",
        "ground cinnamon": "молотая корица",
        "ground nutmeg": "молотый мускатный орех",
        "ground allspice": "молотый душистый перец",
        "ground cloves": "молотая гвоздика",
        "instant coffee": "растворимый кофе",
        "unsalted butter": "несолёное сливочное масло",
        "buttermilk": "пахта",
        "cornmeal": "кукурузная мука",
        "cornstarch": "кукурузный крахмал",
        "confectioners sugar": "сахарная пудра",
        "peppermint": "перечная мята",
        "food coloring": "пищевой краситель",
    },
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
    system_prompt = (
        "You are a professional culinary translator. "
        "Provide natural, context-aware translations and return only the translated text."
    )
    if dest == 'uz':
        system_prompt += " Use Uzbek in the Latin alphabet."
    elif dest == 'ru':
        system_prompt += " Use standard Russian culinary terminology."
    messages = [
        {"role": "system", "content": system_prompt},
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


def _chatgpt_translate_recipe(data: dict, dest: str) -> Optional[dict]:
    """Translate an entire recipe JSON blob with ChatGPT and return dict."""
    if not openai:
        print("OpenAI package not installed; cannot translate recipe via ChatGPT")
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set; cannot translate recipe via ChatGPT")
        return None

    language = LANGUAGE_NAMES.get(dest, dest)
    system_prompt = (
        "You are a professional culinary translator. Always provide natural, "
        "context-aware, and correct translations suitable for home cooks. "
        f"Translate the following recipe data from English to {language}. "
        "Never translate word-for-word; always give complete, natural, and meaningful sentences. "
        "Return only the translated JSON object, nothing else."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
    ]

    try:  # pragma: no cover - network
        if hasattr(openai, "ChatCompletion"):
            openai.api_key = api_key
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0,
            )
            content = completion.choices[0].message["content"].strip()
        elif OpenAI:
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0,
            )
            content = completion.choices[0].message.content.strip()
        else:
            return None
        return json.loads(content)
    except Exception as exc:
        print(f"ChatGPT recipe translation failed: {exc}")
        return None


def apply_translations(recipe):
    """Translate and populate all recipe fields using a single ChatGPT call per language."""
    languages = ['uz', 'ru']

    categories = list(recipe.categories.all())
    ingredients = list(recipe.ingredients.all())
    steps = list(recipe.instructions.order_by('step_number'))

    base_data = {
        "name": recipe.name,
        "description": recipe.description,
        "categories": [c.name for c in categories],
        "ingredients": [
            {"name": ing.name, "amount": ing.amount or ""} for ing in ingredients
        ],
        "steps": [step.description for step in steps],
    }

    for lang in languages:
        translated = _chatgpt_translate_recipe(base_data, lang)
        if not translated:
            continue

        setattr(recipe, f"name_{lang}", translated.get("name", recipe.name))
        setattr(
            recipe,
            f"description_{lang}",
            translated.get("description", recipe.description),
        )

        cat_trans = translated.get("categories", [])
        for cat_obj, name in zip(categories, cat_trans):
            setattr(cat_obj, f"name_{lang}", name or cat_obj.name)

        ing_trans = translated.get("ingredients", [])
        for ing_obj, item in zip(ingredients, ing_trans):
            if isinstance(item, dict):
                name = item.get("name")
            else:
                name = None
            if name:
                setattr(ing_obj, f"name_{lang}", name)

        step_trans = translated.get("steps", [])
        for step_obj, text in zip(steps, step_trans):
            if isinstance(text, dict):
                desc = text.get("description")
            else:
                desc = text
            if desc:
                setattr(step_obj, f"description_{lang}", desc)

    recipe.save()
    for obj in categories + ingredients + steps:
        obj.save()

