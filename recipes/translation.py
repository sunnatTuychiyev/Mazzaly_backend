from modeltranslation.translator import register, TranslationOptions
from .models import Category, MealType, Recipe, Ingredient, Instruction

@register(Category)
class CategoryTO(TranslationOptions):
    fields = ('name',)

@register(MealType)
class MealTypeTO(TranslationOptions):
    fields = ('name',)

@register(Recipe)
class RecipeTO(TranslationOptions):
    fields = ('name', 'description',)

@register(Ingredient)
class IngredientTO(TranslationOptions):
    fields = ('name',)

@register(Instruction)
class InstructionTO(TranslationOptions):
    fields = ('description',)
