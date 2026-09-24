"""SONAR-X Report Models"""

from django.db import models
from django.conf import settings
import uuid


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('SURVEY', 'Survey Report'),
        ('TEMPORAL', 'Temporal Intelligence Report'),
        ('EVALUATION', 'Evaluation Report'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey('surveys.Survey', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    report_type = models.CharField(max_length=15, choices=REPORT_TYPE_CHOICES, default='SURVEY')
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    parameters = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sonarx_reports'
        ordering = ['-timestamp']
