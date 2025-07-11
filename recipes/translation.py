from modeltranslation.translator import translator, TranslationOptions
from .models import Recipe, Ingredient, Instruction, Category, MealType

class RecipeTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

class IngredientTranslationOptions(TranslationOptions):
    fields = ('name',)

class InstructionTranslationOptions(TranslationOptions):
    fields = ('description',)

class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

class MealTypeTranslationOptions(TranslationOptions):
    fields = ('name',)

translator.register(Recipe, RecipeTranslationOptions)
translator.register(Ingredient, IngredientTranslationOptions)
translator.register(Instruction, InstructionTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(MealType, MealTypeTranslationOptions)
