from typing import Dict, List

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


def build_multilingual_payload(recipe) -> Dict[str, Dict[str, any]]:
    """Build a multilingual representation using stored translation fields."""
    languages = ['en', 'uz', 'ru']
    payload: Dict[str, Dict[str, any]] = {}
    for lang in languages:
        payload[lang] = {
            'id': recipe.id,
            'name': getattr(recipe, f'name_{lang}', recipe.name),
            'description': getattr(recipe, f'description_{lang}', recipe.description),
            'prep_time': recipe.prep_time,
            'cook_time': recipe.cook_time,
            'servings': recipe.servings,
            'healthy': recipe.healthy,
            'calories': recipe.calories,
            'protein': recipe.protein,
            'fats': recipe.fats,
            'carbs': recipe.carbs,
            'categories': [getattr(cat, f'name_{lang}', cat.name) for cat in recipe.categories.all()],
            'ingredients': [
                {
                    'name': getattr(ing, f'name_{lang}', ing.name),
                    'amount': ing.amount,
                    'unit': ing.unit,
                    'preparation': ing.preparation,
                }
                for ing in recipe.ingredients.all()
            ],
            'instructions': [
                {
                    'step_number': step.step_number,
                    'description': getattr(step, f'description_{lang}', step.description),
                }
                for step in recipe.instructions.all()
            ],
        }
    return payload
