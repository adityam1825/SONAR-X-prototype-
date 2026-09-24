"""SONAR-X Sonar File Models"""

from django.db import models
from django.conf import settings
import uuid
import os


def sonar_upload_path(instance, filename):
    """Secure upload path for sonar files."""
    import re
    # Sanitize filename
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', os.path.basename(filename))
    return f"sonar_files/{instance.survey.survey_id}/{safe_name}"


class SonarFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('PNG', 'PNG Image'),
        ('JPG', 'JPEG Image'),
        ('TIFF', 'TIFF Image'),
        ('DEMO', 'Demo Synthetic Image'),
    ]
    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('VALIDATING', 'Validating'),
        ('VALID', 'Valid'),
        ('WARNING', 'Valid with Warnings'),
        ('INVALID', 'Invalid'),
        ('PREPROCESSING', 'Preprocessing'),
        ('PREPROCESSED', 'Preprocessed'),
        ('FAILED', 'Failed'),
    ]
    CHANNEL_CHOICES = [
        ('PORT', 'Port'),
        ('STARBOARD', 'Starboard'),
        ('BOTH', 'Both'),
        ('UNKNOWN', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey('surveys.Survey', on_delete=models.CASCADE, related_name='sonar_files')
    file = models.ImageField(upload_to=sonar_upload_path, null=True, blank=True)
    demo_image_key = models.CharField(max_length=100, blank=True, help_text='Key for bundled demo images')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='PNG')
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    is_grayscale = models.BooleanField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPLOADED')

    # Sonar metadata (overrides survey-level if present)
    altitude_m = models.FloatField(null=True, blank=True)
    range_scale_mpp = models.FloatField(null=True, blank=True)
    pixel_scale_gpp = models.FloatField(null=True, blank=True, help_text='Ground range per pixel after correction')
    channel_layout = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='UNKNOWN')
    already_gain_corrected = models.BooleanField(null=True, blank=True)
    already_slant_range_corrected = models.BooleanField(null=True, blank=True)
    already_processed = models.BooleanField(null=True, blank=True)

    # Quality
    quality_score = models.FloatField(null=True, blank=True)
    quality_level = models.CharField(max_length=20, blank=True)
    saturation_ratio = models.FloatField(null=True, blank=True)
    dropout_ratio = models.FloatField(null=True, blank=True)
    snr_proxy = models.FloatField(null=True, blank=True)
    nadir_width_px = models.IntegerField(null=True, blank=True)
    image_contrast = models.FloatField(null=True, blank=True)
    usable_area_ratio = models.FloatField(null=True, blank=True)

    # Processed image path
    processed_file = models.ImageField(upload_to='sonar_processed/', null=True, blank=True)

    is_demo = models.BooleanField(default=False)
    data_source = models.CharField(max_length=10, default='SURVEY')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sonarx_sonar_files'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} ({self.survey.survey_id})"


class ProcessingLog(models.Model):
    STEP_CHOICES = [
        ('INGESTION', 'Data Ingestion'),
        ('VALIDATION', 'Validation'),
        ('NADIR', 'Nadir Gap Handling'),
        ('GAIN', 'Gain Correction'),
        ('SLANT_RANGE', 'Slant-Range Correction'),
        ('NOISE', 'Noise Reduction'),
        ('CONTRAST', 'Contrast Enhancement'),
        ('QUALITY', 'Quality Assessment'),
        ('DETECTION', 'Candidate Detection'),
        ('FINGERPRINT', 'Sonar Fingerprint'),
        ('FUSION', 'Evidence Fusion'),
        ('CLASSIFICATION', 'Classification'),
        ('HAZARD', 'Hazard Assessment'),
        ('GEOLOCATION', 'Geolocation'),
        ('TEMPORAL', 'Temporal Tracking'),
    ]
    STATUS_CHOICES = [
        ('APPLIED', 'Applied'),
        ('ESTIMATED', 'Estimated'),
        ('SKIPPED', 'Skipped'),
        ('FAILED', 'Failed'),
        ('COMPLETE', 'Complete'),
        ('NOT_APPLIED', 'Not Applied'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(SonarFile, on_delete=models.CASCADE, related_name='processing_logs')
    step = models.CharField(max_length=30, choices=STEP_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    parameters = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    output_summary = models.JSONField(default=dict, blank=True)
    software_version = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sonarx_processing_logs'
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.file.filename} | {self.step} | {self.status}"


class ValidationResult(models.Model):
    RESULT_CHOICES = [
        ('VALID', 'Valid'),
        ('WARNING', 'Valid with Warnings'),
        ('INVALID', 'Invalid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.OneToOneField(SonarFile, on_delete=models.CASCADE, related_name='validation_result')
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    checks = models.JSONField(default=list)
    warnings = models.JSONField(default=list)
    errors = models.JSONField(default=list)
    saturation_ratio = models.FloatField(null=True, blank=True)
    dropout_ratio = models.FloatField(null=True, blank=True)
    nadir_detected = models.BooleanField(null=True, blank=True)
    signal_quality = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sonarx_validation_results'
