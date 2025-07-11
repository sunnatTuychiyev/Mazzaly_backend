from modeltranslation.translator import register, TranslationOptions
from .models import Category, MealType, Recipe, Ingredient, Instruction

@register(Category)
class CategoryTR(TranslationOptions):
    fields = ('name',)

@register(MealType)
class MealTypeTR(TranslationOptions):
    fields = ('name',)

@register(Recipe)
class RecipeTR(TranslationOptions):
    fields = ('name', 'description',)

@register(Ingredient)
class IngredientTR(TranslationOptions):
    fields = ('name', 'preparation',)

@register(Instruction)
class InstructionTR(TranslationOptions):
    fields = ('description',)
