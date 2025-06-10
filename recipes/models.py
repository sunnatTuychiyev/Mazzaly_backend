from django.db import models
from django.conf import settings

# --- CATEGORY ---
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# --- MEAL TYPE ---
class MealType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# --- RECIPE ---
class Recipe(models.Model):
    healthy = models.BooleanField(default=False, help_text="Show as Healthy Recipe")
    calories = models.PositiveIntegerField(blank=True, null=True, help_text="Calories in kcal (optional)")
    protein = models.PositiveIntegerField(blank=True, null=True, help_text="Protein in grams (optional)")
    fats = models.PositiveIntegerField(blank=True, null=True, help_text="Fats in grams (optional)")
    carbs = models.PositiveIntegerField(blank=True, null=True, help_text="Carbs in grams (optional)")

    name = models.CharField(max_length=255)
    categories = models.ManyToManyField(Category, blank=True, related_name='recipes')

    description = models.TextField()
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    prep_time = models.PositiveIntegerField(help_text="in minutes")
    cook_time = models.PositiveIntegerField(help_text="in minutes")
    servings = models.PositiveIntegerField()
    #tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags like 'healthy,vegetarian'")
    

    def __str__(self):
        return self.name

# --- INGREDIENT ---
class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ingredients', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, blank=True, null=True)
    preparation = models.CharField(max_length=100, blank=True, null=True, help_text="Optional: large, grated, cubed, etc.")

    def __str__(self):
        return f"{self.amount} {self.unit} {self.name}"

# --- INSTRUCTION ---
class Instruction(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='instructions', on_delete=models.CASCADE)
    step_number = models.PositiveIntegerField()
    description = models.TextField()

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number}: {self.description[:50]}..."

# --- MEAL PLAN ---
class MealPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meal_plans')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    meal_type = models.ForeignKey(MealType, on_delete=models.SET_NULL, null=True, related_name='meal_plans')
    scheduled_time = models.DateTimeField()

    def __str__(self):
        return f"{self.user} - {self.recipe} - {self.meal_type} at {self.scheduled_time}"

# --- SHOPPING LIST ITEM ---
class ShoppingListItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_list')
    name = models.CharField(max_length=255)
    amount = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)
    checked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.amount} {self.unit} {self.name} ({'done' if self.checked else 'pending'})"

# --- RECIPE RATING (kelajak uchun) ---
class RecipeRating(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # 1-5
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} rated {self.recipe} as {self.rating}"
