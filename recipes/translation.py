from modeltranslation.translator import register, TranslationOptions
from .models import Recipe, Ingredient, Instruction, Category, MealType

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(MealType)
class MealTypeTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Recipe)
class RecipeTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

@register(Ingredient)
class IngredientTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Instruction)
class InstructionTranslationOptions(TranslationOptions):
    fields = ('description',)
