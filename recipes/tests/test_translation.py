from unittest.mock import Mock, patch
from django.test import SimpleTestCase, override_settings

from recipes.translation_chatgpt import translate_list


class TranslateListTests(SimpleTestCase):
    @patch('recipes.translation_chatgpt.requests.post')
    @override_settings(OPENAI_API_KEY='key')
    def test_translate_list(self, mock_post):
        def response(content: str) -> Mock:
            m = Mock()
            m.status_code = 200
            m.json.return_value = {
                'choices': [{'message': {'content': content}}]
            }
            return m

        mock_post.side_effect = [response('hola'), response('mundo')]

        result = translate_list(['hello', 'world'], 'es')
        self.assertEqual(result, ['hola', 'mundo'])
        self.assertEqual(mock_post.call_count, 2)
        first_call = mock_post.call_args_list[0]
        headers = first_call.kwargs['headers']
        payload = first_call.kwargs['json']
        self.assertEqual(headers['Authorization'], 'Bearer key')
        self.assertEqual(payload['model'], 'gpt-4o-mini')
        self.assertEqual(payload['messages'][0]['role'], 'system')
