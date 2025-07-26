from django.urls import path
from .views import statistics_data

urlpatterns = [
    path('statistics/data/', statistics_data, name='statistics-data'),
]
