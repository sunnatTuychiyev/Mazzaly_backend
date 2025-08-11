from django.test import SimpleTestCase

from recipes.importers.themealdb import TheMealDBImporter


class ThemealDBImporterTests(SimpleTestCase):
    def test_normalize(self):
        importer = TheMealDBImporter()
        raw = {
            'idMeal': '1',
            'strMeal': 'Cake',
            'strCategory': 'Dessert',
            'strIngredient1': 'Sugar',
            'strMeasure1': '1 cup',
            'strInstructions': 'Mix\nBake',
            'strMealThumb': 'http://img',
        }
        normalized = importer.normalize(raw)
        self.assertEqual(normalized['source_id'], '1')
        self.assertEqual(normalized['name'], 'Cake')
        self.assertEqual(normalized['categories'], ['Dessert'])
        self.assertEqual(normalized['ingredients'], ['1 cup Sugar'])
        self.assertEqual(normalized['steps'], ['Mix', 'Bake'])
        self.assertEqual(normalized['image_url'], 'http://img')
