from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Recipe, Ingredient, Instruction
from .translation import translate_text

LANGS = ['uz', 'ru']

@receiver(post_save, sender=Recipe)
def auto_translate_recipe(sender, instance, created, **kwargs):
    if not created:
        return
    updated = False
    for lang in LANGS:
        name_field = f'name_{lang}'
        desc_field = f'description_{lang}'
        if hasattr(instance, name_field) and not getattr(instance, name_field):
            setattr(instance, name_field, translate_text(instance.name, lang))
            updated = True
        if hasattr(instance, desc_field) and not getattr(instance, desc_field):
            setattr(instance, desc_field, translate_text(instance.description, lang))
            updated = True
    if updated:
        instance.save()
    # ingredients
    for ing in instance.ingredients.all():
        ing_updated = False
        for lang in LANGS:
            f_name = f'name_{lang}'
            if hasattr(ing, f_name) and not getattr(ing, f_name):
                setattr(ing, f_name, translate_text(ing.name, lang))
                ing_updated = True
        if ing_updated:
            ing.save()
    # instructions
    for step in instance.instructions.all():
        step_updated = False
        for lang in LANGS:
            f_desc = f'description_{lang}'
            if hasattr(step, f_desc) and not getattr(step, f_desc):
                setattr(step, f_desc, translate_text(step.description, lang))
                step_updated = True
        if step_updated:
            step.save()


@receiver(post_save, sender=Ingredient)
def auto_translate_ingredient(sender, instance, created, **kwargs):
    if not created:
        return
    updated = False
    for lang in LANGS:
        f_name = f'name_{lang}'
        if hasattr(instance, f_name) and not getattr(instance, f_name):
            setattr(instance, f_name, translate_text(instance.name, lang))
            updated = True
    if updated:
        instance.save()


@receiver(post_save, sender=Instruction)
def auto_translate_instruction(sender, instance, created, **kwargs):
    if not created:
        return
    updated = False
    for lang in LANGS:
        f_desc = f'description_{lang}'
        if hasattr(instance, f_desc) and not getattr(instance, f_desc):
            setattr(instance, f_desc, translate_text(instance.description, lang))
            updated = True
    if updated:
        instance.save()
