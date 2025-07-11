from django.conf import settings
from google.cloud import translate_v2 as translate

_translate_client = None

def get_client():
    global _translate_client
    if _translate_client is None:
        _translate_client = translate.Client()
    return _translate_client

SUPPORTED_LANGUAGES = [lang for lang in getattr(settings, 'MODELTRANSLATION_LANGUAGES', []) if lang != 'en']

def translate_text(text: str, target: str) -> str:
    if not text:
        return ''
    client = get_client()
    result = client.translate(text, source_language='en', target_language=target)
    return result['translatedText']


def translate_recipe(instance):
    for lang in SUPPORTED_LANGUAGES:
        instance.name = instance.name  # ensure en field is saved
        setattr(instance, f'name_{lang}', translate_text(instance.name, lang))
        setattr(instance, f'description_{lang}', translate_text(instance.description, lang))
    instance.save()
    for ingredient in instance.ingredients.all():
        for lang in SUPPORTED_LANGUAGES:
            setattr(ingredient, f'name_{lang}', translate_text(ingredient.name, lang))
        ingredient.save()
    for step in instance.instructions.all():
        for lang in SUPPORTED_LANGUAGES:
            setattr(step, f'description_{lang}', translate_text(step.description, lang))
        step.save()
