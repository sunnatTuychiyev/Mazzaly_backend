import io
from django.contrib import admin, messages
from django.core.management import call_command
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from django.contrib.admin.helpers import ActionForm

from .forms import EdamamImportForm, SpoonacularImportForm, TheMealDBImportForm
from .models import (
    Category,
    MealType,
    Recipe,
    Ingredient,
    Instruction,
    MealPlan,
    ShoppingListItem,
    RecipeRating,
    RecipeSubmission,
    RecipeSubmissionImage,
    UserRecipe,
)

# Category va MealType’ni admin panelga qo‘shish


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["display_name", "name_uz", "name_ru"]
    fields = ["name_uz", "name_ru"]
    exclude = ("name",)

    def display_name(self, obj):
        uz = obj.name_uz or obj.name
        ru = obj.name_ru or obj.name
        return f"{uz} / {ru}"

    display_name.short_description = "UZ / RU"

    def save_model(self, request, obj, form, change):
        # Ensure canonical name is set from Uzbek (fallback to Russian)
        if not obj.name:
            obj.name = (obj.name_uz or obj.name_ru or obj.name or "").strip()
        super().save_model(request, obj, form, change)


admin.site.register(MealType)


# Ingredient va Instruction inlines faqat uzbek va rus tilida
class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ["name_uz", "name_ru", "amount", "unit_uz", "unit_ru", "preparation"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name_uz"].required = True
        self.fields["name_ru"].required = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.name = self.cleaned_data.get("name_uz", "")
        obj.unit = self.cleaned_data.get("unit_uz") or ""
        if commit:
            obj.save()
        return obj


class IngredientInline(admin.TabularInline):
    model = Ingredient
    form = IngredientForm
    extra = 1
    fields = ["name_uz", "name_ru", "amount", "unit_uz", "unit_ru", "preparation"]


class InstructionForm(forms.ModelForm):
    class Meta:
        model = Instruction
        fields = ["step_number", "description_uz", "description_ru"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description_uz"].required = True
        self.fields["description_ru"].required = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.description = self.cleaned_data.get("description_uz", "")
        if commit:
            obj.save()
        return obj


class InstructionInline(admin.TabularInline):
    model = Instruction
    form = InstructionForm
    extra = 1
    fields = ["step_number", "description_uz", "description_ru"]


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            "name_uz",
            "name_ru",
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
            "author",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name_uz"].required = True
        self.fields["name_ru"].required = True
        self.fields["description_uz"].required = True
        self.fields["description_ru"].required = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.name = self.cleaned_data.get("name_uz", "")
        obj.description = self.cleaned_data.get("description_uz", "")
        if commit:
            obj.save()
            self.save_m2m()
        return obj


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
    inlines = [IngredientInline, InstructionInline]
    list_display = ["name_uz", "name_ru", "subscription_plan", "get_categories"]
    list_filter = ["subscription_plan"]
    fields = [
        "name_uz",
        "name_ru",
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
        "author",
    ]
    filter_horizontal = ["categories"]

    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])

    get_categories.short_description = "Categories"

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
                    line.replace("Added ", "")
                    for line in output
                    if line.startswith("Added ")
                ]
                recipes = Recipe.objects.filter(name__in=added)
                context = {
                    "recipes": recipes,
                    "output": output,
                    "opts": self.model._meta,
                }
                return render(request, "admin/recipes/import_result.html", context)
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
                    line.replace("Added ", "")
                    for line in output
                    if line.startswith("Added ")
                ]
                recipes = Recipe.objects.filter(name__in=added)
                context = {
                    "recipes": recipes,
                    "output": output,
                    "opts": self.model._meta,
                }
                return render(request, "admin/recipes/import_result.html", context)
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
                    line.replace("Added ", "")
                    for line in output
                    if line.startswith("Added ")
                ]
                recipes = Recipe.objects.filter(name__in=added)
                context = {
                    "recipes": recipes,
                    "output": output,
                    "opts": self.model._meta,
                }
                return render(request, "admin/recipes/import_result.html", context)
        else:
            form = TheMealDBImportForm()
        context = {
            "form": form,
            "opts": self.model._meta,
            "title": "Add TheMealDB Recipes",
        }
        return render(request, "admin/recipes/import_form.html", context)


class SubmissionActionForm(ActionForm):
    note = forms.CharField(required=False, label="Moderator note")


class RecipeSubmissionImageInline(admin.TabularInline):
    model = RecipeSubmissionImage
    extra = 1


class RecipeSubmissionAdminForm(forms.ModelForm):
    instructions = forms.JSONField(required=False, label="Instructions")

    class Meta:
        model = RecipeSubmission
        exclude = ("steps",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["instructions"].initial = self.instance.steps

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.steps = self.cleaned_data.get("instructions", [])
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(RecipeSubmission)
class RecipeSubmissionAdmin(admin.ModelAdmin):
    inlines = [RecipeSubmissionImageInline]
    form = RecipeSubmissionAdminForm
    list_display = ("name", "user", "status", "created_at")
    fields = [
        "user",
        "name",
        "name_uz",
        "name_ru",
        "description",
        "description_uz",
        "description_ru",
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
        "ingredients",
        "instructions",
    ]
    filter_horizontal = ["categories"]
    actions = ["approve_submissions", "reject_submissions"]
    action_form = SubmissionActionForm

    def get_readonly_fields(self, request, obj=None):
        base = super().get_readonly_fields(request, obj)
        if obj:
            return base + ("user",)
        return base

    @admin.action(description="Approve selected submissions")
    def approve_submissions(self, request, queryset):
        for sub in queryset:
            sub.approve()
        self.message_user(request, "Selected submissions approved.")

    @admin.action(description="Reject selected submissions")
    def reject_submissions(self, request, queryset):
        note = request.POST.get("note", "")
        for sub in queryset:
            sub.reject(note)
        self.message_user(request, "Selected submissions rejected.")


admin.site.register(MealPlan)
admin.site.register(ShoppingListItem)
admin.site.register(RecipeRating)


@admin.register(UserRecipe)
class UserRecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "owner__email")
