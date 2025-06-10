from rest_framework.routers import DefaultRouter
from .views import (
    RecipeViewSet, MealPlanViewSet, ShoppingListItemViewSet,
    IngredientListView, CategoryViewSet, MealTypeViewSet,
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'meal-plan', MealPlanViewSet, basename='mealplan')
router.register(r'shopping-list', ShoppingListItemViewSet, basename='shoppinglist')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'mealtypes', MealTypeViewSet, basename='mealtype')

urlpatterns = router.urls

# Ingredient qidiruv/avto-complete uchun
from django.urls import path
urlpatterns += [
    path('ingredients/', IngredientListView.as_view(), name='ingredient-list'),
]
