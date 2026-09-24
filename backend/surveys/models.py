"""SONAR-X Survey Models"""

from django.db import models
from django.conf import settings
import uuid


class Survey(models.Model):
    DATA_SOURCE_CHOICES = [
        ('DEMO', 'Demo Data'),
        ('SURVEY', 'Real Survey Data'),
    ]
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('UPLOADING', 'Uploading'),
        ('UPLOADED', 'Uploaded'),
        ('VALIDATING', 'Validating'),
        ('VALIDATED', 'Validated'),
        ('PREPROCESSING', 'Preprocessing'),
        ('PREPROCESSED', 'Preprocessed'),
        ('ANALYZING', 'Analyzing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    CHANNEL_CHOICES = [
        ('PORT', 'Port'),
        ('STARBOARD', 'Starboard'),
        ('BOTH', 'Both'),
    ]

    survey_id = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=200)
    date = models.DateField()
    area = models.CharField(max_length=200, blank=True)
    operator = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='surveys'
    )
    data_source = models.CharField(max_length=10, choices=DATA_SOURCE_CHOICES, default='SURVEY')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')

    # Sonar metadata
    altitude_m = models.FloatField(null=True, blank=True, help_text='Altitude above seabed in metres')
    range_scale_mpp = models.FloatField(null=True, blank=True, help_text='Slant-range scale: metres per pixel')
    channel_layout = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='BOTH')
    already_gain_corrected = models.BooleanField(default=False)
    already_slant_range_corrected = models.BooleanField(default=False)
    already_processed = models.BooleanField(default=False)

    # Location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sonarx_surveys'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.survey_id}: {self.name}"

    def save(self, *args, **kwargs):
        if not self.survey_id:
            import datetime
            date_str = self.date.strftime('%Y%m%d') if self.date else datetime.date.today().strftime('%Y%m%d')
            base = f"SX-SRV-{date_str}"
            # Find next available ID
            existing = Survey.objects.filter(survey_id__startswith=base).count()
            self.survey_id = f"{base}-{existing + 1:03d}"
        super().save(*args, **kwargs)

    @property
    def detection_count(self):
        return self.detections.count()
