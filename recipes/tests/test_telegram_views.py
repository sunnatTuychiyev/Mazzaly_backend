from django.urls import reverse
from django.test import TestCase


class TelegramRecipeFormAccessTests(TestCase):
    def test_requires_telegram_user_agent(self):
        url = reverse("telegram-recipe-form")
        res = self.client.get(url, HTTP_USER_AGENT="Mozilla/5.0")
        self.assertEqual(res.status_code, 403)

    def test_allows_telegram_user_agent(self):
        url = reverse("telegram-recipe-form")
        res = self.client.get(url, HTTP_USER_AGENT="TelegramWebApp")
        self.assertEqual(res.status_code, 200)

