import io
from django.contrib import admin, messages
from django.core.management import call_command
from django.shortcuts import render, redirect
from django.urls import path

from .forms import (
    EdamamImportForm,
    SpoonacularImportForm,
    TheMealDBImportForm,
    ChatGPTImportForm,
)
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
    filter_horizontal = ['categories']

    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])

    get_categories.short_description = 'Categories'

    def get_urls(self):  # pragma: no cover - admin registration
        urls = super().get_urls()
        custom = [
            path(
                "import-edamam/",
                self.admin_site.admin_view(self.import_edamam),
                name="recipes_recipe_import_edamam",
            ),
            path(
                "import-spoonacular/",
                self.admin_site.admin_view(self.import_spoonacular),
                name="recipes_recipe_import_spoonacular",
            ),
            path(
                "import-themealdb/",
                self.admin_site.admin_view(self.import_themealdb),
                name="recipes_recipe_import_themealdb",
            ),
            path(
                "import-chatgpt/",
                self.admin_site.admin_view(self.import_chatgpt),
                name="recipes_recipe_import_chatgpt",
            ),
        ]
        return custom + urls

    def import_edamam(self, request):  # pragma: no cover - simple admin view
        if request.method == "POST":
            if "confirm" in request.POST:
                ids = request.POST.getlist("delete")
                if ids:
                    Recipe.objects.filter(id__in=ids).delete()
                    messages.success(request, f"Deleted {len(ids)} recipes.")
                else:
                    messages.success(request, "All recipes kept.")
                return redirect("..")
            form = EdamamImportForm(request.POST)
            if form.is_valid():
                count = form.cleaned_data["count"]
                query = form.cleaned_data.get("query")
                meal_type = form.cleaned_data.get("meal_type")
                out = io.StringIO()
                try:
                    call_command(
                        "add_edamam_recipes",
                        count,
                        query=query,
                        meal_type=meal_type,
                        stdout=out,
                        no_color=True,
                    )
                except Exception as exc:
                    messages.error(request, str(exc))
                    return redirect("..")
                output = out.getvalue().splitlines()
                added = [
                    line.replace("Added ", "") for line in output if line.startswith("Added ")
                ]
                recipes = Recipe.objects.filter(name__in=added)
                context = {
                    "recipes": recipes,
                    "output": output,
                    "opts": self.model._meta,
                }
                return render(
                    request, "admin/recipes/import_result.html", context
                )
        else:
            form = EdamamImportForm()
        context = {
            "form": form,
            "opts": self.model._meta,
            "title": "Add Edamam Recipes",
        }
        return render(request, "admin/recipes/import_form.html", context)

    def import_spoonacular(self, request):  # pragma: no cover - simple admin view
        if request.method == "POST":
            if "confirm" in request.POST:
                ids = request.POST.getlist("delete")
                if ids:
                    Recipe.objects.filter(id__in=ids).delete()
                    messages.success(request, f"Deleted {len(ids)} recipes.")
                else:
                    messages.success(request, "All recipes kept.")
                return redirect("..")
            form = SpoonacularImportForm(request.POST)
            if form.is_valid():
                count = form.cleaned_data["count"]
                tags = form.cleaned_data.get("tags")
                meal_type = form.cleaned_data.get("meal_type")
                out = io.StringIO()
                try:
                    call_command(
                        "fetch_spoonacular",
                        number=count,
                        tags=tags,
                        meal_type=meal_type,
                        stdout=out,
                        no_color=True,
                    )
                except Exception as exc:
                    messages.error(request, str(exc))
                    return redirect("..")
                output = out.getvalue().splitlines()
                added = [
                    line.replace("Added ", "") for line in output if line.startswith("Added ")
                ]
                recipes = Recipe.objects.filter(name__in=added)
                context = {
                    "recipes": recipes,
                    "output": output,
                    "opts": self.model._meta,
                }
                return render(
                    request, "admin/recipes/import_result.html", context
                )
        else:
            form = SpoonacularImportForm()
        context = {
            "form": form,
            "opts": self.model._meta,
            "title": "Add Spoonacular Recipes",
        }
        return render(request, "admin/recipes/import_form.html", context)

    def import_themealdb(self, request):  # pragma: no cover - simple admin view
        if request.method == "POST":
            if "confirm" in request.POST:
                ids = request.POST.getlist("delete")
                if ids:
                    Recipe.objects.filter(id__in=ids).delete()
                    messages.success(request, f"Deleted {len(ids)} recipes.")
                else:
                    messages.success(request, "All recipes kept.")
                return redirect("..")
            form = TheMealDBImportForm(request.POST)
            if form.is_valid():
                search_term = form.cleaned_data.get("search_term", "")
                count = form.cleaned_data["count"]
                tags = form.cleaned_data.get("tags")
                meal_type = form.cleaned_data.get("meal_type")
                out = io.StringIO()
                try:
                    call_command(
                        "add_themealdb_recipes",
                        search_term,
                        count=count,
                        tags=tags,
                        meal_type=meal_type,
                        stdout=out,
                        no_color=True,
                    )
                except Exception as exc:
                    messages.error(request, str(exc))
                    return redirect("..")
                output = out.getvalue().splitlines()
                added = [
                    line.replace("Added ", "") for line in output if line.startswith("Added ")
                ]
                recipes = Recipe.objects.filter(name__in=added)
                context = {
                    "recipes": recipes,
                    "output": output,
                    "opts": self.model._meta,
                }
                return render(
                    request, "admin/recipes/import_result.html", context
                )
        else:
            form = TheMealDBImportForm()
        context = {
            "form": form,
            "opts": self.model._meta,
            "title": "Add TheMealDB Recipes",
        }
        return render(request, "admin/recipes/import_form.html", context)

    def import_chatgpt(self, request):  # pragma: no cover - simple admin view
        if request.method == "POST":
            if "confirm" in request.POST:
                ids = request.POST.getlist("delete")
                if ids:
                    Recipe.objects.filter(id__in=ids).delete()
                    messages.success(request, f"Deleted {len(ids)} recipes.")
                else:
                    messages.success(request, "All recipes kept.")
                return redirect("..")
            form = ChatGPTImportForm(request.POST)
            if form.is_valid():
                search_term = form.cleaned_data.get("search_term", "")
                count = form.cleaned_data["count"]
                tags = form.cleaned_data.get("tags")
                meal_type = form.cleaned_data.get("meal_type")
                out = io.StringIO()
                try:
                    call_command(
                        "import_chatgpt_recipes",
                        search_term=search_term,
                        count=count,
                        tags=tags,
                        meal_type=meal_type,
                        stdout=out,
                        no_color=True,
                    )
                except Exception as exc:
                    messages.error(request, str(exc))
                    return redirect("..")
                output = out.getvalue().splitlines()
                added = [
                    line.replace("Added ", "") for line in output if line.startswith("Added ")
                ]
                recipes = Recipe.objects.filter(name__in=added)
                context = {
                    "recipes": recipes,
                    "output": output,
                    "opts": self.model._meta,
                }
                return render(
                    request, "admin/recipes/import_result.html", context
                )
        else:
            form = ChatGPTImportForm()
        context = {
            "form": form,
            "opts": self.model._meta,
            "title": "Add ChatGPT Recipes",
        }
        return render(request, "admin/recipes/import_form.html", context)




admin.site.register(MealPlan)
admin.site.register(ShoppingListItem)
admin.site.register(RecipeRating)
