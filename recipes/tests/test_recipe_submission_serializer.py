from django.test import TestCase
from django.contrib.auth import get_user_model

from recipes.serializers import RecipeSubmissionSerializer


class RecipeSubmissionSerializerTests(TestCase):
    def test_ingredients_and_steps_are_optional(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="user", password="pass")

        data = {
            "name": "Test recipe",
            "description": "Desc",
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
