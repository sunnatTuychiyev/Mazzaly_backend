from django.contrib import admin
from .models import (
    Category,
    MealType,
    Recipe,
    Ingredient,
    Instruction,
    MealPlan,
    ShoppingListItem,
    RecipeRating,
)

# Category va MealType’ni admin panelga qo‘shish

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "name_uz", "name_ru"]
    fields = ["name", "name_uz", "name_ru"]


admin.site.register(MealType)

# Ingredient va Instruction inlines
class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 1
    fields = [
        "name",
        "name_uz",
        "name_ru",
        "amount",
        "unit",
        "preparation",
    ]
    
class InstructionInline(admin.TabularInline):
    model = Instruction
    extra = 1
    fields = [
        "step_number",
        "description",
        "description_uz",
        "description_ru",
    ]

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngredientInline, InstructionInline]
    list_display = ["name", "name_uz", "name_ru", "subscription_plan", "get_categories"]
    list_filter = ["subscription_plan"]
    fields = [
        "name",
        "name_uz",
        "name_ru",
        "description",
        "description_uz",
        "description_ru",
        "image",
        "prep_time",
        "cook_time",
        "servings",
        "subscription_plan",
        "healthy",
        "calories",
        "protein",
        "fats",
        "carbs",
        "categories",
    ]
    filter_horizontal = ['categories']  # <-- faqat shu qatorni qo‘shing!
    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = 'Categories'




admin.site.register(MealPlan)
admin.site.register(ShoppingListItem)
admin.site.register(RecipeRating)
