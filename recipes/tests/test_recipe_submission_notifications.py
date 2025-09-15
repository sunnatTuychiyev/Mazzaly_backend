from django.test import TestCase, override_settings
from unittest.mock import patch

from account.models import User
from recipes.models import RecipeSubmission, Category


class RecipeSubmissionNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            first_name="User",
            last_name="Test",
            password="strongpass123",
        )
        self.user.telegram_id = "12345"
        self.user.save()
        self.category = Category.objects.create(name="Dessert")

    @override_settings(TELEGRAM_BOT_TOKEN="123:ABC")
    @patch("recipes.signals.requests.post")
    def test_notify_on_approval(self, mock_post):
        sub = RecipeSubmission.objects.create(
            user=self.user,
            name="Cake",
            name_uz="Tort",
            name_ru="Торт",
            description="desc",
            description_uz="desc uz",
            description_ru="desc ru",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=RecipeSubmission.PLAN_STANDARD,
            ingredients=[],
            steps=[],
        )
        sub.categories.add(self.category)
        sub.approve()
        self.assertTrue(mock_post.called)
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["chat_id"], self.user.telegram_id)
        self.assertIn("qabul qilindi", payload["text"])

    @override_settings(TELEGRAM_BOT_TOKEN="123:ABC")
    @patch("recipes.signals.requests.post")
    def test_notify_on_rejection(self, mock_post):
        sub = RecipeSubmission.objects.create(
            user=self.user,
            name="Soup",
            name_uz="Sho'rva",
            name_ru="Суп",
            description="desc",
            description_uz="desc uz",
            description_ru="desc ru",
            prep_time=1,
            cook_time=1,
            servings=1,
            subscription_plan=RecipeSubmission.PLAN_STANDARD,
            ingredients=[],
            steps=[],
        )
        sub.reject()
        self.assertTrue(mock_post.called)
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["chat_id"], self.user.telegram_id)
        self.assertIn("rad etildi", payload["text"])
