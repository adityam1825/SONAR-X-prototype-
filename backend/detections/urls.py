from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'debris', views.DebrisObjectViewSet, basename='debris')
router.register(r'', views.DetectionViewSet, basename='detection')

urlpatterns = [
    path('', include(router.urls)),
]
