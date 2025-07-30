from django.urls import reverse
from rest_framework.test import APITestCase
from analytics.models import SiteVisit


class SiteVisitTests(APITestCase):
    def test_visit_logged_when_listing_cards(self):
        url = reverse('recipecard-list')
        self.client.get(url)
        assert SiteVisit.objects.count() == 1
