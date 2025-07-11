from modeltranslation.translator import register, TranslationOptions
from .models import Category, MealType, Recipe, Ingredient, Instruction

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(MealType)
class MealTypeTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Recipe)
class RecipeTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

@register(Ingredient)
class IngredientTranslationOptions(TranslationOptions):
    fields = ('name', 'preparation', 'unit')

@register(Instruction)
class InstructionTranslationOptions(TranslationOptions):
    fields = ('description',)
