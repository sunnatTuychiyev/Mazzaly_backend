from django.urls import reverse
from rest_framework.test import APITestCase
from unittest.mock import patch
from io import BytesIO
from PIL import Image

from recipes.models import Recipe, Ingredient, Instruction
from account.models import Subscription


class ChatbotTests(APITestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            name="Omelet",
            description="Desc",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=Subscription.PLAN_STANDARD,
        )
        Ingredient.objects.create(recipe=self.recipe, name="egg", amount="1")
        Ingredient.objects.create(recipe=self.recipe, name="cheese", amount="1")
        Instruction.objects.create(recipe=self.recipe, step_number=1, description="Beat eggs")
        Instruction.objects.create(recipe=self.recipe, step_number=2, description="Cook with cheese")

    @patch("chatbot.services.hf_generate_reply", return_value="fallback")
    def test_message_returns_local_recipe(self, mock_hf):
        url = reverse("chatbot-message")
        res = self.client.post(url, {"message": "How do I make omelet?"}, format="json")
        assert res.status_code == 200
        assert "Beat eggs" in res.data["reply"]
        assert self.recipe.id in res.data["suggested_recipes"]

    @patch("chatbot.services.hf_analyze_image", return_value=("pizza", 280))
    def test_image_endpoint(self, mock_hf):
        image = Image.new("RGB", (10, 10), color="red")
        buf = BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        url = reverse("chatbot-image")
        res = self.client.post(url, {"image": buf}, format="multipart")
        assert res.status_code == 200
        assert res.data == {"predicted_food": "pizza", "estimated_kcal": 280}


