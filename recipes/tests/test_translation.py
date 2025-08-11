from unittest.mock import patch
from django.test import SimpleTestCase, override_settings

from recipes.translation_google import translate_list


class TranslateListTests(SimpleTestCase):
    @patch('recipes.translation_google.requests.post')
    @override_settings(GOOGLE_TRANSLATE_API_KEY='key')
    def test_translate_list(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'data': {'translations': [{'translatedText': 'hola'}, {'translatedText': 'mundo'}]}
        }
        result = translate_list(['hello', 'world'], 'es')
        self.assertEqual(result, ['hola', 'mundo'])
        self.assertTrue(mock_post.called)
        payload = mock_post.call_args.kwargs['json']
        params = mock_post.call_args.kwargs['params']
        self.assertEqual(params['key'], 'key')
        self.assertEqual(payload['source'], 'en')
        self.assertEqual(payload['target'], 'es')
        self.assertEqual(payload['q'], ['hello', 'world'])
