from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings

class ChatViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_no_api_key(self):
        if hasattr(settings, 'OPENAI_API_KEY'):
            delattr(settings, 'OPENAI_API_KEY')
        response = self.client.post(reverse('ai-chat'), {'message': 'Hello'})
        self.assertEqual(response.status_code, 503)
