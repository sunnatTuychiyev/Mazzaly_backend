from django.db.models.signals import post_save
from django.dispatch import receiver
from google.cloud import translate_v2 as translate
from .models import Recipe, Ingredient, Instruction, Category

translator = translate.Client()
TARGET_LANGS = ['ru', 'uz']

def _translate(text: str, lang: str) -> str:
    if not text:
        return ''
    result = translator.translate(text, target_language=lang)
    return result.get('translatedText')

@receiver(post_save, sender=Recipe)
def translate_recipe(sender, instance: Recipe, **kwargs):
    updates = {}
    for lang in TARGET_LANGS:
        name_field = f'name_{lang}'
        desc_field = f'description_{lang}'
        if not getattr(instance, name_field):
            updates[name_field] = _translate(instance.name, lang)
        if not getattr(instance, desc_field):
            updates[desc_field] = _translate(instance.description, lang)
    if updates:
        Recipe.objects.filter(pk=instance.pk).update(**updates)

    # categories
    for cat in instance.categories.all():
        cat_updates = {}
        for lang in TARGET_LANGS:
            field = f'name_{lang}'
            if not getattr(cat, field):
                cat_updates[field] = _translate(cat.name, lang)
        if cat_updates:
            Category.objects.filter(pk=cat.pk).update(**cat_updates)

    # ingredients
    for ing in instance.ingredients.all():
        ing_updates = {}
        for lang in TARGET_LANGS:
            name_field = f'name_{lang}'
            prep_field = f'preparation_{lang}'
            if not getattr(ing, name_field):
                ing_updates[name_field] = _translate(ing.name, lang)
            if ing.preparation and not getattr(ing, prep_field):
                ing_updates[prep_field] = _translate(ing.preparation, lang)
        if ing_updates:
            Ingredient.objects.filter(pk=ing.pk).update(**ing_updates)

    # instructions
    for instr in instance.instructions.all():
        inst_updates = {}
        for lang in TARGET_LANGS:
            field = f'description_{lang}'
            if not getattr(instr, field):
                inst_updates[field] = _translate(instr.description, lang)
        if inst_updates:
            Instruction.objects.filter(pk=instr.pk).update(**inst_updates)
