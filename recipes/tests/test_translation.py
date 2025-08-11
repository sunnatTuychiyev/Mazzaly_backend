from unittest.mock import patch
from django.test import SimpleTestCase, override_settings

from recipes.translation_yandex import translate_list


class TranslateListTests(SimpleTestCase):
    @patch('recipes.translation_yandex.requests.post')
    @override_settings(YANDEX_TRANSLATE_API_KEY='key')
    def test_translate_list(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'translations': [{'text': 'hola'}, {'text': 'mundo'}]
        }
        result = translate_list(['hello', 'world'], 'es')
        self.assertEqual(result, ['hola', 'mundo'])
        self.assertTrue(mock_post.called)
        payload = mock_post.call_args.kwargs['json']
        self.assertEqual(payload['sourceLanguageCode'], 'en')
        self.assertEqual(payload['targetLanguageCode'], 'es')
        self.assertEqual(payload['texts'], ['hello', 'world'])
