from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from account.models import User, Subscription
from recipes.models import Recipe, Ingredient, Instruction, ShoppingListItem, MealPlan, MealType
import datetime
from django.utils import timezone
from unittest.mock import patch

class RecipeSubscriptionTests(APITestCase):
    def setUp(self):
        # Create recipes for each tier
        self.standard_recipe = Recipe.objects.create(
            name="Standard",
            description="Standard desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        Ingredient.objects.create(recipe=self.standard_recipe, name="i", amount="1")
        Instruction.objects.create(recipe=self.standard_recipe, step_number=1, description="d")

        self.healthy_recipe = Recipe.objects.create(
            name="Healthy",
            description="Healthy desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_HEALTHY,
        )
        Ingredient.objects.create(recipe=self.healthy_recipe, name="i", amount="1")
        Instruction.objects.create(recipe=self.healthy_recipe, step_number=1, description="d")

        self.premium_recipe = Recipe.objects.create(
            name="Premium",
            description="Premium desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_PREMIUM,
        )
        Ingredient.objects.create(recipe=self.premium_recipe, name="i", amount="1")
        Instruction.objects.create(recipe=self.premium_recipe, step_number=1, description="d")

        # Users with different subscriptions
        self.healthy_user = User.objects.create_user(
            email="healthy@example.com",
            first_name="Healthy",
            last_name="User",
            password="StrongPass1",
        )
        Subscription.objects.create(user=self.healthy_user, plan=Subscription.PLAN_HEALTHY)

        self.premium_user = User.objects.create_user(
            email="premium@example.com",
            first_name="Premium",
            last_name="User",
            password="StrongPass1",
        )
        Subscription.objects.create(user=self.premium_user, plan=Subscription.PLAN_PREMIUM)

    def _get_data(self, response):
        data = response.data
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data

    def _get_ids(self, response):
        return {item["id"] for item in self._get_data(response)}

    def test_anonymous_only_gets_standard(self):
        url = reverse("recipe-list")
        res = self.client.get(url)
        ids = self._get_ids(res)
        assert self.standard_recipe.id in ids
        assert self.healthy_recipe.id not in ids
        assert self.premium_recipe.id not in ids

    def test_healthy_user_gets_standard_and_healthy(self):
        self.client.force_authenticate(self.healthy_user)
        url = reverse("recipe-list")
        res = self.client.get(url)
        ids = self._get_ids(res)
        assert self.standard_recipe.id in ids
        assert self.healthy_recipe.id in ids
        assert self.premium_recipe.id not in ids

    def test_premium_user_gets_all(self):
        self.client.force_authenticate(self.premium_user)
        url = reverse("recipe-list")
        res = self.client.get(url)
        ids = self._get_ids(res)
        assert self.standard_recipe.id in ids
        assert self.healthy_recipe.id in ids
        assert self.premium_recipe.id in ids

    def test_auth_header_without_bearer(self):
        token = str(AccessToken.for_user(self.healthy_user))
        url = reverse("recipe-list")
        res = self.client.get(url, HTTP_AUTHORIZATION=token)
        ids = self._get_ids(res)
        assert self.standard_recipe.id in ids
        assert self.healthy_recipe.id in ids
        assert self.premium_recipe.id not in ids

    def test_updating_plan_updates_flags(self):
        recipe = Recipe.objects.create(
            name="Change Me",
            description="desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        recipe.subscription_plan = Subscription.PLAN_PREMIUM
        recipe.save()
        recipe.refresh_from_db()
        assert recipe.subscription_plan == Subscription.PLAN_PREMIUM
        assert recipe.premium is True
        assert recipe.healthy is False

    def test_detail_requires_authentication(self):
        url = reverse("recipe-detail", args=[self.standard_recipe.id])
        res = self.client.get(url)
        assert res.status_code == 401

    def test_insufficient_subscription_returns_403(self):
        self.client.force_authenticate(self.healthy_user)
        url = reverse("recipe-detail", args=[self.premium_recipe.id])
        res = self.client.get(url)
        assert res.status_code == 403

    def test_allowed_user_can_retrieve(self):
        self.client.force_authenticate(self.healthy_user)
        url = reverse("recipe-detail", args=[self.healthy_recipe.id])
        res = self.client.get(url)
        assert res.status_code == 200
        assert res.data["id"] == self.healthy_recipe.id


class RecipeCardAPITests(APITestCase):
    def setUp(self):
        self.standard_recipe = Recipe.objects.create(
            name="Standard",
            description="Standard desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        Ingredient.objects.create(recipe=self.standard_recipe, name="i", amount="1")
        Instruction.objects.create(recipe=self.standard_recipe, step_number=1, description="d")

        self.healthy_recipe = Recipe.objects.create(
            name="Healthy",
            description="Healthy desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_HEALTHY,
        )
        Ingredient.objects.create(recipe=self.healthy_recipe, name="i", amount="1")
        Instruction.objects.create(recipe=self.healthy_recipe, step_number=1, description="d")

        self.premium_recipe = Recipe.objects.create(
            name="Premium",
            description="Premium desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_PREMIUM,
        )
        Ingredient.objects.create(recipe=self.premium_recipe, name="i", amount="1")
        Instruction.objects.create(recipe=self.premium_recipe, step_number=1, description="d")

        self.healthy_user = User.objects.create_user(
            email="healthy2@example.com",
            first_name="Healthy",
            last_name="User",
            password="StrongPass1",
        )
        Subscription.objects.create(user=self.healthy_user, plan=Subscription.PLAN_HEALTHY)

        self.premium_user = User.objects.create_user(
            email="premium2@example.com",
            first_name="Premium",
            last_name="User",
            password="StrongPass1",
        )
        Subscription.objects.create(user=self.premium_user, plan=Subscription.PLAN_PREMIUM)

    def _get_data(self, response):
        data = response.data
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data

    def _get_ids(self, response):
        return {item["id"] for item in self._get_data(response)}

    def test_card_fields(self):
        url = reverse("recipecard-list")
        res = self.client.get(url)
        assert res.status_code == 200
        item = self._get_data(res)[0]
        expected_keys = {
            "id",
            "name",
            "categories",
            "description",
            "image",
            "prep_time",
            "cook_time",
            "subscription_plan",
            "views",
        }
        assert expected_keys.issubset(item.keys())

    def test_returns_all_recipes(self):
        url = reverse("recipecard-list")
        res = self.client.get(url)
        ids = self._get_ids(res)
        assert self.standard_recipe.id in ids
        assert self.healthy_recipe.id in ids
        assert self.premium_recipe.id in ids

        self.client.force_authenticate(self.healthy_user)
        res = self.client.get(url)
        ids = self._get_ids(res)
        assert self.standard_recipe.id in ids
        assert self.healthy_recipe.id in ids
        assert self.premium_recipe.id in ids

        self.client.force_authenticate(self.premium_user)
        res = self.client.get(url)
        ids = self._get_ids(res)
        assert self.standard_recipe.id in ids
        assert self.healthy_recipe.id in ids
        assert self.premium_recipe.id in ids

    def test_detail_increments_views_and_shows_in_cards(self):
        self.client.force_authenticate(self.premium_user)
        detail_url = reverse("recipe-detail", args=[self.standard_recipe.id])
        initial = self.standard_recipe.views
        res = self.client.get(detail_url)
        assert res.status_code == 200
        self.standard_recipe.refresh_from_db()
        assert self.standard_recipe.views == initial + 1

        cards_url = reverse("recipecard-list")
        res = self.client.get(cards_url)
        data = self._get_data(res)
        card = next(item for item in data if item["id"] == self.standard_recipe.id)
        assert card["views"] == self.standard_recipe.views


class ShoppingListAddRecipeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="shopper@example.com",
            first_name="Shopper",
            last_name="User",
            password="StrongPass1",
        )
        Subscription.objects.create(user=self.user, plan=Subscription.PLAN_PREMIUM)
        self.recipe = Recipe.objects.create(
            name="Banana",
            description="desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        Ingredient.objects.create(
            recipe=self.recipe,
            name="very ripe banana",
            name_uz="pishgan banan",
            amount="1",
        )

        self.fraction_recipe = Recipe.objects.create(
            name="Half Banana",
            description="desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        Ingredient.objects.create(
            recipe=self.fraction_recipe, name="very ripe banana", amount="1/2"
        )

        self.decimal_recipe = Recipe.objects.create(
            name="Decimal Banana",
            description="desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        Ingredient.objects.create(
            recipe=self.decimal_recipe, name="very ripe banana", amount="0,5"
        )

    def test_duplicate_add_accumulates_amount(self):
        self.client.force_authenticate(self.user)
        url = reverse("shoppinglist-add-recipe-ingredients")
        data = {"recipe_id": self.recipe.id}
        res1 = self.client.post(url, data, format="json")
        assert res1.status_code == 200
        item = ShoppingListItem.objects.get(
            user=self.user, name="very ripe banana"
        )
        assert item.amount == "1"
        res2 = self.client.post(url, data, format="json")
        assert res2.status_code == 200
        item.refresh_from_db()
        assert item.amount == "2"

    def test_duplicate_fraction_add_accumulates_amount(self):
        self.client.force_authenticate(self.user)
        url = reverse("shoppinglist-add-recipe-ingredients")
        data = {"recipe_id": self.fraction_recipe.id}
        res1 = self.client.post(url, data, format="json")
        assert res1.status_code == 200
        item = ShoppingListItem.objects.get(
            user=self.user, name="very ripe banana"
        )
        assert item.amount == "1/2"
        res2 = self.client.post(url, data, format="json")
        assert res2.status_code == 200
        item.refresh_from_db()
        assert item.amount == "1"

    def test_duplicate_decimal_add_accumulates_amount(self):
        self.client.force_authenticate(self.user)
        url = reverse("shoppinglist-add-recipe-ingredients")
        data = {"recipe_id": self.decimal_recipe.id}
        res1 = self.client.post(url, data, format="json")
        assert res1.status_code == 200
        item = ShoppingListItem.objects.get(
            user=self.user, name="very ripe banana",
        )
        assert item.amount == "0,5"
        res2 = self.client.post(url, data, format="json")
        assert res2.status_code == 200
        item.refresh_from_db()
        assert item.amount == "1"

    def test_add_recipe_respects_language(self):
        self.client.force_authenticate(self.user)
        url = reverse("shoppinglist-add-recipe-ingredients") + "?lang=uz"
        data = {"recipe_id": self.recipe.id}
        res = self.client.post(url, data, format="json")
        assert res.status_code == 200
        assert ShoppingListItem.objects.filter(
            user=self.user, name="pishgan banan"
        ).exists()


class MealPlanLanguageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="planner@example.com",
            first_name="Planner",
            last_name="User",
            password="StrongPass1",
        )
        Subscription.objects.create(user=self.user, plan=Subscription.PLAN_PREMIUM)
        self.recipe = Recipe.objects.create(
            name="Banana",
            name_uz="Banan",
            name_ru="Банан",
            description="desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        self.meal_type = MealType.objects.create(name="Breakfast")
        MealPlan.objects.create(
            user=self.user,
            recipe=self.recipe,
            meal_type=self.meal_type,
            scheduled_time=timezone.make_aware(datetime.datetime(2024, 1, 1, 7, 30)),
        )

    def test_by_date_returns_translated_recipe_name(self):
        self.client.force_authenticate(self.user)
        url = reverse("mealplan-by-date", kwargs={"date": "2024-01-01"})
        res = self.client.get(url + "?lang=uz")
        assert res.status_code == 200
        meal = next(m for m in res.data["meals"] if m["recipe"])
        assert meal["recipe"]["name"] == "Banan"

    def test_create_returns_translated_recipe_name(self):
        self.client.force_authenticate(self.user)
        url = reverse("mealplan-list") + "?lang=uz"
        data = {
            "date": "2025-08-15",
            "type": "Breakfast",
            "time": "19:00",
            "recipe_id": self.recipe.id,
            "custom_meal": None,
        }
        res = self.client.post(url, data, format="json")
        assert res.status_code == 201
        assert res.data["recipe"]["name"] == "Banan"

    def test_create_with_ru_lang_returns_russian_name(self):
        self.client.force_authenticate(self.user)
        url = reverse("mealplan-list") + "?lang=ru"
        data = {
            "date": "2025-08-15",
            "type": "Breakfast",
            "time": "19:00",
            "recipe_id": self.recipe.id,
            "custom_meal": None,
        }
        res = self.client.post(url, data, format="json")
        assert res.status_code == 201
        assert res.data["recipe"]["name"] == "Банан"

    def test_create_falls_back_to_translation(self):
        self.client.force_authenticate(self.user)
        recipe = Recipe.objects.create(
            name="Test Meal",
            description="desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        MealType.objects.create(name="Dinner")
        url = reverse("mealplan-list") + "?lang=ru"
        data = {
            "date": "2025-08-15",
            "type": "Dinner",
            "time": "19:00",
            "recipe_id": recipe.id,
            "custom_meal": None,
        }
        with patch("recipes.translation_utils.translate_text", side_effect=lambda text, lang: f"{text}-{lang}"):
            res = self.client.post(url, data, format="json")
        assert res.status_code == 201
        assert res.data["recipe"]["name"] == "Test Meal-ru"

