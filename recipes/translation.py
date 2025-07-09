from typing import Dict, List, Any

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


def translate_full_recipe(recipe, dest: str) -> Dict[str, Any]:
    """Return a full recipe dictionary translated to the given language."""
    from .serializers import RecipeSerializer

    data = RecipeSerializer(recipe).data
    data['name'] = translate_text(recipe.name, dest)
    data['description'] = translate_text(recipe.description, dest)
    # translate ingredient names
    data['ingredients'] = [
        {
            **ing,
            'name': translate_text(ing['name'], dest)
        }
        for ing in data.get('ingredients', [])
    ]
    # translate instruction descriptions
    data['instructions'] = [
        {
            **step,
            'description': translate_text(step['description'], dest)
        }
        for step in data.get('instructions', [])
    ]
    # translate category names
    data['categories'] = [
        {
            'id': cat['id'],
            'name': translate_text(cat['name'], dest)
        }
        for cat in data.get('categories', [])
    ]
    return data


def get_recipe_multilang(recipe) -> Dict[str, Dict[str, Any]]:
    """Return English, Uzbek and Russian versions of a recipe."""
    from .serializers import RecipeSerializer

    eng_data = RecipeSerializer(recipe).data
    uz_data = translate_full_recipe(recipe, 'uz')
    ru_data = translate_full_recipe(recipe, 'ru')
    return {
        'eng': eng_data,
        'uz': uz_data,
        'ru': ru_data,
    }
