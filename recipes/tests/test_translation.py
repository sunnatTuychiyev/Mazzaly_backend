from unittest.mock import patch
from django.test import SimpleTestCase

from recipes.translation_yandex import translate_list


class TranslateListTests(SimpleTestCase):
    @patch('recipes.translation_yandex.requests.post')
    def test_translate_list(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'translations': [{'text': 'hola'}, {'text': 'mundo'}]
        }
        result = translate_list(['hello', 'world'], 'es')
        self.assertEqual(result, ['hola', 'mundo'])
        self.assertTrue(mock_post.called)
