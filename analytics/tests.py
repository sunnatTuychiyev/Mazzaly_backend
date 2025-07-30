from django.urls import reverse
from rest_framework.test import APITestCase
from analytics.models import RecipeCardVisit
from recipes.models import Recipe
from account.models import Subscription


class RecipeCardVisitTests(APITestCase):
    def setUp(self):
        Recipe.objects.create(
            name="R1",
            description="d",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )

    def test_unique_visit_logged_once_per_hour(self):
        url = reverse("recipecard-list")
        self.client.get(url, HTTP_USER_AGENT="Agent")
        self.client.get(url, HTTP_USER_AGENT="Agent")
        assert RecipeCardVisit.objects.count() == 1
