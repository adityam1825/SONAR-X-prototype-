from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .ingest import ingest_survey

router = DefaultRouter()
router.register(r'', views.SurveyViewSet, basename='survey')

urlpatterns = [
    path('ingest/', ingest_survey, name='ingest_survey'),
    path('', include(router.urls)),
]
