from django.test import TestCase
from django.contrib.auth import get_user_model

from recipes.serializers import RecipeSubmissionSerializer


class RecipeSubmissionSerializerTests(TestCase):
    def test_ingredients_and_instructions_are_optional(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="user", password="pass")

        data = {
            "name_uz": "Test recipe",
            "name_ru": "Тестовый рецепт",
            "description_uz": "Desc uz",
            "description_ru": "Desc ru",
            "prep_time": 5,
            "cook_time": 10,
            "servings": 2,
            "subscription_plan": "standard",
        }

        serializer = RecipeSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        submission = serializer.save(user=user)
        self.assertEqual(submission.ingredients, [])
        self.assertEqual(submission.steps, [])
        self.assertEqual(submission.name, "Test recipe")
        self.assertEqual(submission.description, "Desc uz")

    def test_accepts_unit_translations(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="user2", password="pass")

        data = {
            "name_uz": "Test recipe",
            "name_ru": "Тестовый рецепт",
            "description_uz": "Desc uz",
            "description_ru": "Desc ru",
            "prep_time": 5,
            "cook_time": 10,
            "servings": 2,
            "subscription_plan": "standard",
            "ingredients": [
                {
                    "name_uz": "Sugar",
                    "name_ru": "Сахар",
                    "unit_uz": "g",
                    "unit_ru": "г",
                    "amount": "100",
                }
            ],
        }

        serializer = RecipeSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        submission = serializer.save(user=user)
        self.assertEqual(submission.ingredients[0]["unit_ru"], "г")
        self.assertEqual(submission.ingredients[0]["unit_uz"], "g")
        self.assertEqual(submission.ingredients[0]["name"], "Sugar")
