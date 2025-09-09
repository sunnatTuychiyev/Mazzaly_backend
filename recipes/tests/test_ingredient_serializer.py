from django.test import TestCase

from recipes.models import Recipe, Ingredient
from recipes.serializers import IngredientSerializer


class IngredientSerializerTests(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            name="Test",
            description="Desc",
            prep_time=1,
            cook_time=1,
            servings=1,
        )

    def test_unit_translations(self):
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name="Milk",
            unit="cup",
            unit_ru="стакан",
            unit_uz="stakan",
            amount="1",
        )

        data_en = IngredientSerializer(ingredient).data
        self.assertEqual(data_en["unit"], "cup")
        self.assertEqual(data_en["unit_ru"], "стакан")
        self.assertEqual(data_en["unit_uz"], "stakan")

        data_ru = IngredientSerializer(ingredient, context={"lang": "ru"}).data
        self.assertEqual(data_ru["unit"], "стакан")

        data_uz = IngredientSerializer(ingredient, context={"lang": "uz"}).data
        self.assertEqual(data_uz["unit"], "stakan")

    def test_create_with_unit_translations(self):
        payload = {
            "name": "Sugar",
            "unit": "tbsp",
            "unit_ru": "ст. л.",
            "unit_uz": "osh qoshiq",
            "amount": "2",
        }
        serializer = IngredientSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        ingredient = serializer.save(recipe=self.recipe)
        self.assertEqual(ingredient.unit_ru, "ст. л.")
        self.assertEqual(ingredient.unit_uz, "osh qoshiq")
