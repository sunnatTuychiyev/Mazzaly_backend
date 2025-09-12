from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile

from recipes.models import Category, RecipeSubmission


class TelegramRecipeSubmissionCreateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('telegram-recipe-submission-create')
        self.category = Category.objects.create(name='TestCat')

    @patch('recipes.telegram_views.get_user_from_init_data')
    def test_submit_single_category_with_image(self, mock_get_user):
        user = get_user_model().objects.create_user(username='user', password='pass')
        mock_get_user.return_value = user

        image = SimpleUploadedFile('test.jpg', b'filecontent', content_type='image/jpeg')
        data = {
            'init_data': 'stub',
            'name_uz': 'Recipe uz',
            'name_ru': 'Recipe ru',
            'description_uz': 'Desc uz',
            'description_ru': 'Desc ru',
            'prep_time': 1,
            'cook_time': 1,
            'servings': 1,
            'subscription_plan': 'standard',
            'categories': str(self.category.id),
            'images': image,
        }

        resp = self.client.post(self.url, data, format='multipart')
        self.assertEqual(resp.status_code, 201, resp.content)
        submission = RecipeSubmission.objects.get()
        self.assertEqual(list(submission.categories.values_list('id', flat=True)), [self.category.id])
        self.assertEqual(submission.images.count(), 1)


class TelegramCategoryCreateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('telegram-category-create')

    @patch('recipes.telegram_views.get_user_from_init_data')
    def test_create_category(self, mock_get_user):
        user = get_user_model().objects.create_user(username='cat', password='pass')
        mock_get_user.return_value = user

        data = {
            'init_data': 'stub',
            'name_uz': 'Shirinlik',
            'name_ru': 'Десерт',
        }

        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertTrue(Category.objects.filter(name='Shirinlik', name_uz='Shirinlik', name_ru='Десерт').exists())
