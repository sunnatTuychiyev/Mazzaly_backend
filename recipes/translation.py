from typing import Dict, List

from rest_framework import serializers

try:
    from functools import lru_cache
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


@lru_cache(maxsize=2048)
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


class TranslatableModelSerializer(serializers.ModelSerializer):
    """ModelSerializer that translates fields based on `lang` in context."""
    translatable_fields: List[str] = []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang')
        if lang in {'uz', 'ru'}:
            for field in self.translatable_fields:
                value = data.get(field)
                if isinstance(value, str):
                    data[field] = translate_text(value, lang)
                elif isinstance(value, list):
                    data[field] = [translate_text(v, lang) for v in value]
        return data


class LanguageContextMixin:
    """Mixin for viewsets to expose `lang` query parameter to serializers."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lang'] = self.request.query_params.get('lang')
        return context
