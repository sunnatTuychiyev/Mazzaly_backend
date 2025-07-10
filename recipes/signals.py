from django.db.models.signals import post_save
from django.dispatch import receiver
from modeltranslation.utils import build_localized_fieldname

from .models import Recipe, Ingredient, Instruction, Category, MealType
from .translate_utils import translate_text

LANGS = ['ru', 'uz']

def _set_translation(instance, field, text):
    for lang in LANGS:
        setattr(instance, build_localized_fieldname(field, lang), translate_text(text, lang))

@receiver(post_save, sender=Category)
@receiver(post_save, sender=MealType)
def translate_simple_name(sender, instance, created, **kwargs):
    if created:
        _set_translation(instance, 'name', instance.name)
        instance.save(update_fields=[build_localized_fieldname('name', lang) for lang in LANGS])

@receiver(post_save, sender=Ingredient)
def translate_ingredient(sender, instance, created, **kwargs):
    if created:
        _set_translation(instance, 'name', instance.name)
        instance.save(update_fields=[build_localized_fieldname('name', lang) for lang in LANGS])

@receiver(post_save, sender=Instruction)
def translate_instruction(sender, instance, created, **kwargs):
    if created:
        _set_translation(instance, 'description', instance.description)
        instance.save(update_fields=[build_localized_fieldname('description', lang) for lang in LANGS])

@receiver(post_save, sender=Recipe)
def translate_recipe(sender, instance, created, **kwargs):
    if created:
        _set_translation(instance, 'name', instance.name)
        _set_translation(instance, 'description', instance.description)
        instance.save(update_fields=[build_localized_fieldname('name', lang) for lang in LANGS] +
                                     [build_localized_fieldname('description', lang) for lang in LANGS])
