from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import (
    Category, MealType,
    Recipe, Ingredient, Instruction,
    MealPlan, ShoppingListItem,
    RecipeRating
)

# Category va MealType’ni admin panelga qo‘shish
@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    pass


@admin.register(MealType)
class MealTypeAdmin(TranslationAdmin):
    pass

# Ingredient va Instruction inlines
class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 1
    fields = ['name', 'amount', 'unit', 'preparation']
    
class InstructionInline(admin.TabularInline):
    model = Instruction
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(TranslationAdmin):
    inlines = [IngredientInline, InstructionInline]
    list_display = ['name', 'healthy', 'get_categories']
    filter_horizontal = ['categories']  # <-- faqat shu qatorni qo‘shing!
    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = 'Categories'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from .signals import auto_translate_recipe
        auto_translate_recipe(sender=Recipe, instance=obj, created=not change)




admin.site.register(MealPlan)
admin.site.register(ShoppingListItem)
admin.site.register(RecipeRating)
