from rest_framework import viewsets, permissions, status, filters, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Recipe, Ingredient, MealPlan, ShoppingListItem, Category, MealType
)
from .serializers import (
    RecipeSerializer, IngredientSerializer, IngredientNameSerializer,
    MealPlanSerializer, ShoppingListItemSerializer, CategorySerializer, MealTypeSerializer
)

# --- Category CRUD ---
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

# --- MealType CRUD ---
class MealTypeViewSet(viewsets.ModelViewSet):
    queryset = MealType.objects.all()
    serializer_class = MealTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

# --- Recipe CRUD + Search by Multiple Ingredients ---
class RecipeViewSet(viewsets.ModelViewSet):
    """
    CRUD for recipes, including search by name, categories, and ingredients.
    To search recipes by multiple ingredients:  
    Example: `/api/recipes/?ingredients=egg,milk,flour`
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'categories__name', 'ingredients__name']
    ordering_fields = ['prep_time', 'cook_time', 'servings']
    filterset_fields = ['categories', 'healthy']

    @swagger_auto_schema(
        operation_description="Search recipes by one or more ingredients. "
                              "For example: ?ingredients=egg,milk,flour (all must be in the recipe)",
        manual_parameters=[
            openapi.Parameter(
                'ingredients', openapi.IN_QUERY, 
                description="Comma-separated ingredient names (AND search)", 
                type=openapi.TYPE_STRING
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ingredients_param = request.query_params.get('ingredients')
        if ingredients_param:
            ingredient_names = [i.strip() for i in ingredients_param.split(',') if i.strip()]
            for name in ingredient_names:
                queryset = queryset.filter(ingredients__name__icontains=name)
            queryset = queryset.distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Add all ingredients from a recipe to the current user's shopping list",
        responses={200: openapi.Response('Ingredients added', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'status': openapi.Schema(type=openapi.TYPE_STRING)}
        ))},
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['recipe_id'],
            properties={'recipe_id': openapi.Schema(type=openapi.TYPE_INTEGER)}
        )
    )
    @action(detail=False, methods=['post'], url_path='add-recipe')
    def add_recipe_ingredients(self, request):
        recipe_id = request.data.get('recipe_id')
        if not recipe_id:
            return Response({'error': 'recipe_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)
        for ing in recipe.ingredients.all():
            item, created = ShoppingListItem.objects.get_or_create(
                user=request.user,
                name=ing.name,
                unit=ing.unit,
                defaults={'amount': ing.amount, 'checked': False}
            )
            if not created:
                item.amount = f"{item.amount} + {ing.amount}"
                item.save()
        return Response({'status': 'Ingredients added to shopping list'})

# --- Ingredient autocomplete/search (unique names only) ---
class IngredientListView(generics.ListAPIView):
    serializer_class = IngredientNameSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Autocomplete/search ingredients by name (unique). ?search=onion",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Ingredient name", type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        search = self.request.query_params.get('search')
        qs = Ingredient.objects.all()
        if search:
            qs = qs.filter(name__icontains=search)
        qs = qs.values('name').annotate(id=Min('id'))
        ids = [item['id'] for item in qs]
        return Ingredient.objects.filter(id__in=ids)

# --- MealPlan CRUD (user-scoped) ---
class MealPlanViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MealPlan.objects.none()
        return MealPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# --- Shopping List CRUD (user-scoped) ---
class ShoppingListItemViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingListItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ShoppingListItem.objects.none()
        return ShoppingListItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Add all ingredients from a recipe to user's shopping list (by recipe_id)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['recipe_id'],
            properties={'recipe_id': openapi.Schema(type=openapi.TYPE_INTEGER)}
        ),
        responses={200: 'Ingredients added'}
    )
    @action(detail=False, methods=['post'], url_path='add-recipe')
    def add_recipe_ingredients(self, request):
        recipe_id = request.data.get('recipe_id')
        if not recipe_id:
            return Response({'error': 'recipe_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)
        for ing in recipe.ingredients.all():
            item, created = ShoppingListItem.objects.get_or_create(
                user=request.user,
                name=ing.name,
                unit=ing.unit,
                defaults={'amount': ing.amount, 'checked': False}
            )
            if not created:
                item.amount = f"{item.amount} + {ing.amount}"
                item.save()
        return Response({'status': 'Ingredients added to shopping list'})
