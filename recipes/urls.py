from rest_framework.routers import DefaultRouter
from .views import (
    RecipeViewSet, RecipeCardViewSet,
    MealPlanViewSet, ShoppingListItemViewSet,
    IngredientListView, CategoryViewSet, MealTypeViewSet,
)
from .telegram_views import (
    TelegramRecipeSubmissionCreateView, TelegramRecipeSubmissionMineView,
    TelegramCategoryCreateView
)
from .user_recipe_views import (
    MyRecipeListView, RecipeSubmitView, MyRecipeDetailView,
)


router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'recipe-cards', RecipeCardViewSet, basename='recipecard')
router.register(r'meal-plan', MealPlanViewSet, basename='mealplan')
router.register(r'shopping-list', ShoppingListItemViewSet, basename='shoppinglist')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'mealtypes', MealTypeViewSet, basename='mealtype')
urlpatterns = router.urls

# Ingredient qidiruv/avto-complete uchun
from django.urls import path
urlpatterns += [
    path('ingredients/', IngredientListView.as_view(), name='ingredient-list'),
    path('telegram/recipe-submissions/', TelegramRecipeSubmissionCreateView.as_view(), name='telegram-recipe-submission-create'),
    path('telegram/recipe-submissions/mine/', TelegramRecipeSubmissionMineView.as_view(), name='telegram-recipe-submission-mine'),
    path('telegram/categories/', TelegramCategoryCreateView.as_view(), name='telegram-category-create'),
    path('recipes/my/', MyRecipeListView.as_view(), name='my-recipe-list'),
    path('recipes/submit/', RecipeSubmitView.as_view(), name='recipe-submit'),
    path('recipes/my/<int:pk>/', MyRecipeDetailView.as_view(), name='my-recipe-detail'),
]
