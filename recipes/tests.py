from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from account.models import User, Subscription
from recipes.models import Recipe, Ingredient, Instruction

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

    def _get_ids(self, response):
        return {item["id"] for item in response.data}

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

