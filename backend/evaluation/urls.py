from django.urls import path
from . import views

urlpatterns = [
    path('runs/', views.evaluation_runs, name='evaluation_runs'),
    path('runs/latest/', views.latest_evaluation_run, name='latest_evaluation_run'),
]
