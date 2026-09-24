from django.urls import path
from . import views

urlpatterns = [
    path('', views.temporal_overview, name='temporal_overview'),
    path('<str:debris_uid>/', views.temporal_detail, name='temporal_detail'),
]
