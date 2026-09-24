from django.urls import path
from . import views

urlpatterns = [
    path('surveys/<int:survey_id>/geojson/', views.export_geojson, name='export_geojson'),
    path('surveys/<int:survey_id>/kml/', views.export_kml, name='export_kml'),
    path('surveys/<int:survey_id>/csv/', views.export_csv, name='export_csv'),
    path('surveys/<int:survey_id>/summary/', views.export_summary, name='export_summary'),
]
