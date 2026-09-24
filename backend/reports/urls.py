from django.urls import path
from . import views

urlpatterns = [
    path('surveys/<int:survey_id>/', views.generate_survey_report, name='generate_survey_report'),
    path('temporal/<str:debris_uid>/', views.generate_temporal_report, name='generate_temporal_report'),
    path('download/<uuid:report_id>/', views.download_report, name='download_report'),
]
