"""SONAR-X URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/surveys/', include('surveys.urls')),
    path('api/files/', include('sonar.urls')),
    path('api/detections/', include('detections.urls')),
    path('api/evaluation/', include('evaluation.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/temporal/', include('temporal.urls')),
    path('api/exports/', include('exports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
