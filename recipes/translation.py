from typing import List
from google.cloud import translate_v2 as translate

class TranslationError(Exception):
    """Raised when translation fails."""


def translate_texts(texts: List[str], target_language: str) -> List[str]:
    """Translate a list of texts into the target language using Google API."""
    if not texts:
        return []
    client = translate.Client()
    try:
        result = client.translate(texts, target_language=target_language, format_='text')
    except Exception as exc:  # pragma: no cover - network call
        raise TranslationError(str(exc))
    if isinstance(result, dict):
        result = [result]
    return [r.get('translatedText', '') for r in result]


def translate_recipe_data(data: dict, target_language: str) -> dict:
    """Translate relevant fields of a recipe serializer ``data`` dict."""
    texts: List[str] = []
    # Keep mapping of field paths to index in texts
    mapping: List[tuple] = []

    # Recipe name and description
    mapping.append(('name', len(texts)))
    texts.append(data.get('name', ''))
    mapping.append(('description', len(texts)))
    texts.append(data.get('description', ''))

    # Categories
    for idx, cat in enumerate(data.get('categories', [])):
        mapping.append((f'categories.{idx}.name', len(texts)))
        texts.append(cat.get('name', ''))

    # Ingredients
    for idx, ing in enumerate(data.get('ingredients', [])):
        mapping.append((f'ingredients.{idx}.name', len(texts)))
        texts.append(ing.get('name', ''))
        if ing.get('unit'):
            mapping.append((f'ingredients.{idx}.unit', len(texts)))
            texts.append(ing['unit'])
        if ing.get('preparation'):
            mapping.append((f'ingredients.{idx}.preparation', len(texts)))
            texts.append(ing['preparation'])

    # Instructions
    for idx, inst in enumerate(data.get('instructions', [])):
        mapping.append((f'instructions.{idx}.description', len(texts)))
        texts.append(inst.get('description', ''))

    translations = translate_texts(texts, target_language)

    for field_path, index in mapping:
        translated = translations[index] if index < len(translations) else ''
        parts = field_path.split('.')
        if parts[0] == 'name':
            data['name'] = translated
        elif parts[0] == 'description' and len(parts) == 1:
            data['description'] = translated
        elif parts[0] == 'categories':
            data['categories'][int(parts[1])]['name'] = translated
        elif parts[0] == 'ingredients':
            data['ingredients'][int(parts[1])][parts[2]] = translated
        elif parts[0] == 'instructions':
            data['instructions'][int(parts[1])]['description'] = translated

    return data
