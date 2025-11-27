from rest_framework import viewsets, permissions, status, filters, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
import datetime
from django.db.models import Min, Q, F
from django_filters.rest_framework import DjangoFilterBackend # type: ignore
from fractions import Fraction
import re
try:  # pragma: no cover - drf_yasg optional
    from drf_yasg.utils import swagger_auto_schema
    from drf_yasg import openapi
except Exception:  # pragma: no cover - drf_yasg optional
    def swagger_auto_schema(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func
        return decorator

    class openapi:  # type: ignore
        class Parameter:
            def __init__(self, *args, **kwargs):
                pass

        class Schema:
            def __init__(self, *args, **kwargs):
                pass

        class Response:
            def __init__(self, *args, **kwargs):
                pass

        IN_QUERY = TYPE_STRING = TYPE_OBJECT = TYPE_INTEGER = None


from .models import (
    Recipe, Ingredient, MealPlan, ShoppingListItem, Category, MealType
)
from .serializers import (
    RecipeSerializer, RecipeCardSerializer,
    IngredientSerializer, IngredientNameSerializer,
    MealPlanSerializer, ShoppingListItemSerializer, CategorySerializer,
    MealTypeSerializer, CategoryLocalizedSerializer
)
from .translation_utils import get_requested_lang, SUPPORTED_LANGUAGES
from .permissions import IsHealthySubscriber, IsPremiumSubscriber
from account.models import Subscription


def get_recipes_for_user(user):
    """Return recipes visible for the user's subscription plan."""
    qs = Recipe.objects.all()
    if not user or not user.is_authenticated:
        return qs.filter(subscription_plan=Subscription.PLAN_STANDARD)
    plan = user.current_plan
    if plan == Subscription.PLAN_PREMIUM:
        return qs
    if plan == Subscription.PLAN_HEALTHY:
        return qs.exclude(subscription_plan=Subscription.PLAN_PREMIUM)
    return qs.filter(subscription_plan=Subscription.PLAN_STANDARD)


def _parse_amount(val):
    """Return Fraction representation of the amount or None if unparsable."""
    if val in (None, ""):
        return None
    s = str(val).strip()
    if not s:
        return None
    # Support locales that use commas as decimal separators by normalizing to dots
    s = s.replace(",", ".")
    try:
        return sum(
            Fraction(part)
            for part in re.split(r"\s*\+\s*|\s+", s)
            if part
        )
    except (ValueError, ZeroDivisionError):
        return None

# Shared Swagger parameter for selecting response language
LANG_PARAM = openapi.Parameter(
    'lang',
    openapi.IN_QUERY,
    description='Response language',
    type=openapi.TYPE_STRING,
    enum=SUPPORTED_LANGUAGES,
    default='uz'
)

# --- Category CRUD ---
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'name_uz', 'name_ru']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lang'] = get_requested_lang(self.request)
        return context

    def get_serializer_class(self):
        # For reads, return localized name only: {id, name}
        if self.action in ['list', 'retrieve']:
            return CategoryLocalizedSerializer
        # For writes, use full serializer with name_uz/name_ru fields
        return CategorySerializer

    @action(detail=False, methods=['get'], url_path='all-with-translations')
    def all_with_translations(self, request):
        """Return categories with both name_uz and name_ru for UIs that need both."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer_class = CategorySerializer
        if page is not None:
            serializer = serializer_class(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        serializer = serializer_class(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @swagger_auto_schema(manual_parameters=[LANG_PARAM])
    def list(self, request, *args, **kwargs):  # pragma: no cover - docs only
        """List categories with optional language selection."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=[LANG_PARAM])
    def retrieve(self, request, *args, **kwargs):  # pragma: no cover - docs only
        """Retrieve a single category with optional language selection."""
        return super().retrieve(request, *args, **kwargs)

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
    search_fields = [
        'name', 'name_uz', 'name_ru',
        'categories__name', 'categories__name_uz', 'categories__name_ru',
        'ingredients__name', 'ingredients__name_uz', 'ingredients__name_ru',
    ]
    ordering_fields = ['prep_time', 'cook_time', 'servings']
    filterset_fields = ['categories']

    def get_permissions(self):
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """Return recipes allowed for the current user's subscription."""
        qs = super().get_queryset()
        user = self.request.user

        # Unauthenticated requests only see Standard recipes
        if not user.is_authenticated:
            return qs.filter(subscription_plan=Subscription.PLAN_STANDARD)

        plan = user.current_plan

        # Premium users can see everything
        if plan == Subscription.PLAN_PREMIUM:
            return qs

        # Healthy users see Standard + Healthy recipes
        if plan == Subscription.PLAN_HEALTHY:
            return qs.exclude(subscription_plan=Subscription.PLAN_PREMIUM)

        # Standard or expired subscriptions see only Standard recipes
        return qs.filter(subscription_plan=Subscription.PLAN_STANDARD)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lang'] = get_requested_lang(self.request)
        return context

    @swagger_auto_schema(
        operation_description="Search recipes by one or more ingredients. "
                              "For example: ?ingredients=egg,milk,flour (all must be in the recipe)",
        manual_parameters=[
            openapi.Parameter(
                'ingredients', openapi.IN_QUERY,
                description="Comma-separated ingredient names (AND search)",
                type=openapi.TYPE_STRING
            ),
            LANG_PARAM,
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

    @swagger_auto_schema(manual_parameters=[LANG_PARAM])
    def retrieve(self, request, *args, **kwargs):  # pragma: no cover - docs only
        """Retrieve a recipe in the requested language with subscription check."""
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()
        try:
            recipe = Recipe.objects.get(pk=kwargs.get('pk'))
        except Recipe.DoesNotExist:
            from django.http import Http404
            raise Http404

        plan = request.user.current_plan
        if recipe.subscription_plan == Subscription.PLAN_PREMIUM and plan != Subscription.PLAN_PREMIUM:
            raise PermissionDenied()
        if recipe.subscription_plan == Subscription.PLAN_HEALTHY and plan not in [Subscription.PLAN_HEALTHY, Subscription.PLAN_PREMIUM]:
            raise PermissionDenied()
        Recipe.objects.filter(pk=recipe.pk).update(views=F('views') + 1)
        # Log the view for analytics
        from analytics.models import RecipeViewLog
        ip = request.META.get('REMOTE_ADDR')
        country = ''
        try:
            from django.contrib.gis.geoip2 import GeoIP2
            g = GeoIP2()
            country = g.country(ip)['country_name']
        except Exception:
            country = ''
        RecipeViewLog.objects.create(
            user=request.user,
            recipe=recipe,
            ip_address=ip,
            country=country,
        )
        recipe.refresh_from_db()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data)

class RecipeCardViewSet(RecipeViewSet):
    """Read-only viewset providing simplified recipe data for cards."""
    serializer_class = RecipeCardSerializer
    http_method_names = ['get']

    def get_queryset(self):
        """Return all recipes regardless of user subscription."""
        return Recipe.objects.all()

    @swagger_auto_schema(tags=['recipes'], manual_parameters=[LANG_PARAM])
    def list(self, request, *args, **kwargs):
        # Track unique visitors to the recipe card endpoint
        from analytics.utils import log_recipe_card_visit
        log_recipe_card_visit(request)
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['recipes'], manual_parameters=[LANG_PARAM])
    def retrieve(self, request, *args, **kwargs):
        from analytics.utils import log_recipe_card_visit
        log_recipe_card_visit(request)
        return super().retrieve(request, *args, **kwargs)


# --- Ingredient autocomplete/search (unique names only) ---
class IngredientListView(generics.ListAPIView):
    serializer_class = IngredientNameSerializer
    permission_classes = [IsHealthySubscriber]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lang'] = get_requested_lang(self.request)
        return context

    @swagger_auto_schema(
        operation_description="Autocomplete/search ingredients by name (unique). ?search=onion",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Ingredient name", type=openapi.TYPE_STRING)
        ],
        tags=['recipes']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        search = self.request.query_params.get('search')
        qs = Ingredient.objects.all()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(name_uz__icontains=search)
                | Q(name_ru__icontains=search)
            )
        qs = qs.values('name').annotate(id=Min('id'))
        ids = [item['id'] for item in qs]
        return Ingredient.objects.filter(id__in=ids)

# --- MealPlan CRUD (user-scoped) ---
class MealPlanViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanSerializer
    permission_classes = [IsPremiumSubscriber]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MealPlan.objects.none()
        return MealPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    @swagger_auto_schema(manual_parameters=[LANG_PARAM])
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data.pop('lang', None)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['lang'] = get_requested_lang(self.request)
        return context

    @swagger_auto_schema(manual_parameters=[LANG_PARAM])
    def list(self, request, *args, **kwargs):  # pragma: no cover - docs only
        """List meal plans with optional language selection."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=[LANG_PARAM])
    def retrieve(self, request, *args, **kwargs):  # pragma: no cover - docs only
        """Retrieve a meal plan with optional language selection."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=[LANG_PARAM])
    @action(detail=False, methods=['get'], url_path='planned-dates')
    def planned_dates(self, request):  # pragma: no cover - simple aggregate
        dates = (self.get_queryset()
                 .values_list('scheduled_time', flat=True))
        unique_dates = sorted({dt.date().isoformat() for dt in dates})
        return Response({'planned_dates': unique_dates})

    @swagger_auto_schema(manual_parameters=[LANG_PARAM])
    @action(detail=False, methods=['get'], url_path='date/(?P<date>[^/]+)')
    def by_date(self, request, date=None):
        """Return the meal plan for a given date."""
        try:
            day = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return Response({'error': 'Invalid date'}, status=status.HTTP_400_BAD_REQUEST)

        meal_plans = (self.get_queryset()
                       .filter(scheduled_time__date=day)
                       .select_related('meal_type', 'recipe'))
        plan_map = {mp.meal_type_id: mp for mp in meal_plans}

        default_times = {
            'breakfast': '07:30',
            'lunch': '12:30',
            'dinner': '19:00',
        }

        lang = get_requested_lang(request)
        name_field = f'name_{lang}'
        meals = []
        for meal_type in MealType.objects.all():
            mp = plan_map.get(meal_type.id)
            time = (
                mp.scheduled_time.time().strftime('%H:%M')
                if mp else default_times.get(meal_type.name.lower())
            )
            recipe_data = None
            if mp and mp.recipe:
                name = getattr(mp.recipe, name_field, '').strip()
                if not name or name.lower() == mp.recipe.name.lower():
                    from .translation_utils import translate_text
                    name = translate_text(mp.recipe.name, lang) or mp.recipe.name
                else:
                    name = name or mp.recipe.name
                recipe_data = {'id': mp.recipe.id, 'name': name}
            meal_type_name = meal_type.name
            from .translation_utils import translate_text
            trans = translate_text(meal_type_name, lang)
            if trans:
                meal_type_name = trans
            meals.append({
                'type': meal_type_name,
                'time': time,
                'recipe': recipe_data,
                'custom_meal': mp.custom_meal if mp else None,
            })

        return Response({'date': day.isoformat(), 'meals': meals})

# --- Shopping List CRUD (user-scoped) ---
class ShoppingListItemViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingListItemSerializer
    permission_classes = [IsPremiumSubscriber]

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
        manual_parameters=[LANG_PARAM],
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
        lang = get_requested_lang(request)
        name_field = f'name_{lang}'
        for ing in recipe.ingredients.all():
            ing_name = getattr(ing, name_field, '').strip()
            if not ing_name or ing_name.lower() == ing.name.lower():
                from .translation_utils import translate_text
                ing_name = translate_text(ing.name, lang) or ing.name
            else:
                ing_name = ing_name or ing.name
            amount_val = ing.amount or ""
            item, created = ShoppingListItem.objects.get_or_create(
                user=request.user,
                name=ing_name,
                unit=ing.unit or "",
                defaults={'amount': amount_val, 'checked': False}
            )
            if not created:
                item_amt = _parse_amount(item.amount)
                ing_amt = _parse_amount(ing.amount)
                if item_amt is not None and ing_amt is not None:
                    item.amount = str(item_amt + ing_amt)
                else:
                    item.amount = f"{item.amount} + {(ing.amount or '')}"
                item.save()
        return Response({'status': 'Ingredients added to shopping list'})
