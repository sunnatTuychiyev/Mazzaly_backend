from django.urls import path
from .views import statistics_data, monthly_report_pdf

urlpatterns = [
    path('statistics/data/', statistics_data, name='statistics-data'),
    path('statistics/report/', monthly_report_pdf, name='statistics-report'),
]
