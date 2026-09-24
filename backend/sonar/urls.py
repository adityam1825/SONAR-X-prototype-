from django.urls import path
from . import views

urlpatterns = [
    path('<int:survey_id>/upload/', views.upload_file, name='upload_file'),
    path('<uuid:file_id>/validate/', views.validate_file, name='validate_file'),
    path('<uuid:file_id>/preprocess/', views.preprocess_file, name='preprocess_file'),
    path('<uuid:file_id>/processing-log/', views.processing_log, name='processing_log'),
]
