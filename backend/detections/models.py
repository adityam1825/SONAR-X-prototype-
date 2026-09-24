"""SONAR-X Detection Models"""

from django.db import models
from django.conf import settings
import uuid


class Detection(models.Model):
    CLASS_CHOICES = [
        ('MARINE_DEBRIS', 'Marine Debris'),
        ('NATURAL_FORMATION', 'Natural Formation'),
        ('SONAR_ARTIFACT', 'Sonar Artifact'),
        ('UNKNOWN_ANOMALY', 'Unknown Anomaly'),
    ]
    HAZARD_CHOICES = [
        ('NONE', 'None'),
        ('CAUTION', 'Caution'),
        ('HIGH_CAUTION', 'High Caution'),
    ]
    RISK_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    VERIFICATION_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('ESCALATED', 'Escalated'),
        ('CLASS_CHANGED', 'Class Changed by Reviewer'),
    ]
    INFERENCE_CHOICES = [
        ('DEMO', 'Demo Mode'),
        ('CLASSICAL_CV', 'Classical CV Fallback'),
        ('YOLO', 'YOLO Model'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    detection_uid = models.CharField(max_length=30, unique=True, blank=True)
    survey = models.ForeignKey('surveys.Survey', on_delete=models.CASCADE, related_name='detections')
    sonar_file = models.ForeignKey('sonar.SonarFile', on_delete=models.SET_NULL, null=True, related_name='detections')

    classification = models.CharField(max_length=25, choices=CLASS_CHOICES, default='UNKNOWN_ANOMALY')
    confidence = models.FloatField(default=0.0, help_text='Prototype evidence score 0-100')
    evidence_score = models.FloatField(default=0.0)
    false_positive_risk = models.CharField(max_length=10, choices=RISK_CHOICES, default='MEDIUM')

    # Bounding box (pixel coordinates in processed image)
    bbox_x = models.IntegerField(null=True, blank=True)
    bbox_y = models.IntegerField(null=True, blank=True)
    bbox_w = models.IntegerField(null=True, blank=True)
    bbox_h = models.IntegerField(null=True, blank=True)

    # Geolocation
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    coordinate_source = models.CharField(max_length=50, blank=True,
                                         help_text='Source of coordinate estimate')
    coordinate_note = models.TextField(blank=True)

    # Hazard
    hazard_level = models.CharField(max_length=15, choices=HAZARD_CHOICES, default='NONE')
    hazard_score = models.FloatField(default=0.0)
    hazard_indicators = models.JSONField(default=list)
    hazard_limited_data = models.BooleanField(default=False)
    recommended_action = models.TextField(blank=True)

    # Explainability
    supporting_evidence = models.JSONField(default=list)
    counter_evidence = models.JSONField(default=list)

    # Processing provenance
    inference_mode = models.CharField(max_length=15, choices=INFERENCE_CHOICES, default='DEMO')
    data_source = models.CharField(max_length=10, default='DEMO')
    processing_summary = models.JSONField(default=dict)

    # Verification
    verification_status = models.CharField(max_length=15, choices=VERIFICATION_CHOICES, default='PENDING')
    reviewer_class = models.CharField(max_length=25, blank=True, help_text='Class assigned by reviewer')

    # Temporal
    debris_uid = models.CharField(max_length=20, blank=True)
    temporal_status = models.CharField(max_length=25, blank=True, null=True)

    is_demo = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sonarx_detections'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.detection_uid}: {self.classification} ({self.confidence:.0f}%)"

    def save(self, *args, **kwargs):
        if not self.detection_uid:
            count = Detection.objects.filter(survey=self.survey).count()
            self.detection_uid = f"SX-DET-{self.survey.survey_id}-{count + 1:03d}"
        super().save(*args, **kwargs)


class SonarFingerprint(models.Model):
    STRENGTH_CHOICES = [
        ('STRONG', 'Strong'),
        ('MODERATE', 'Moderate'),
        ('WEAK', 'Weak'),
        ('UNAVAILABLE', 'Unavailable'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    detection = models.OneToOneField(Detection, on_delete=models.CASCADE, related_name='fingerprint')

    backscatter_score = models.FloatField(default=0.0)
    backscatter_status = models.CharField(max_length=15, choices=STRENGTH_CHOICES, default='UNAVAILABLE')

    texture_score = models.FloatField(default=0.0)
    texture_status = models.CharField(max_length=15, choices=STRENGTH_CHOICES, default='UNAVAILABLE')

    geometry_score = models.FloatField(default=0.0)
    geometry_status = models.CharField(max_length=15, choices=STRENGTH_CHOICES, default='UNAVAILABLE')

    shadow_score = models.FloatField(default=0.0)
    shadow_status = models.CharField(max_length=15, choices=STRENGTH_CHOICES, default='UNAVAILABLE')

    object_shadow_score = models.FloatField(default=0.0)
    object_shadow_status = models.CharField(max_length=15, choices=STRENGTH_CHOICES, default='UNAVAILABLE')

    seabed_context_score = models.FloatField(default=0.0)
    seabed_context_status = models.CharField(max_length=15, choices=STRENGTH_CHOICES, default='UNAVAILABLE')

    signal_quality_score = models.FloatField(default=0.0)
    signal_quality_status = models.CharField(max_length=15, choices=STRENGTH_CHOICES, default='UNAVAILABLE')

    evidence_score = models.FloatField(default=0.0)

    raw_features = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sonarx_fingerprints'

    def to_dict(self):
        return {
            'backscatter': self.backscatter_score,
            'texture': self.texture_score,
            'geometry': self.geometry_score,
            'shadow': self.shadow_score,
            'object_shadow': self.object_shadow_score,
            'seabed_context': self.seabed_context_score,
            'signal_quality': self.signal_quality_score,
            'evidence_score': self.evidence_score,
        }


class DebrisObject(models.Model):
    """Tracked debris object across multiple surveys."""
    STATUS_CHOICES = [
        ('STILL_PRESENT', 'Still Present'),
        ('NOT_DETECTED', 'Not Detected'),
        ('POTENTIALLY_RELOCATED', 'Potentially Relocated'),
        ('POSSIBLE_MATCH', 'Possible Match'),
        ('NEW_DETECTION', 'New Detection'),
        ('REQUIRES_VERIFICATION', 'Requires Verification'),
    ]

    debris_uid = models.CharField(max_length=20, unique=True)
    first_observed = models.DateTimeField(auto_now_add=True)
    last_observed = models.DateTimeField(null=True, blank=True)
    current_status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='NEW_DETECTION')
    classification = models.CharField(max_length=25, blank=True)
    hazard_level = models.CharField(max_length=15, default='NONE')
    is_demo = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'sonarx_debris_objects'

    def __str__(self):
        return f"{self.debris_uid} ({self.current_status})"

    def save(self, *args, **kwargs):
        if not self.debris_uid:
            count = DebrisObject.objects.count()
            self.debris_uid = f"SX-DB-{count + 1:04d}"
        super().save(*args, **kwargs)


class DetectionObservation(models.Model):
    """Links a detection to a tracked debris object."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    debris_object = models.ForeignKey(DebrisObject, on_delete=models.CASCADE, related_name='observations')
    survey = models.ForeignKey('surveys.Survey', on_delete=models.CASCADE)
    detection = models.ForeignKey(Detection, on_delete=models.CASCADE, related_name='observations', null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    hazard_level = models.CharField(max_length=15, default='NONE')
    classification = models.CharField(max_length=25, blank=True)
    confidence = models.FloatField(default=0.0)
    fingerprint_snapshot = models.JSONField(default=dict)

    class Meta:
        db_table = 'sonarx_detection_observations'
        ordering = ['timestamp']


class TemporalMatch(models.Model):
    STATUS_CHOICES = [
        ('STILL_PRESENT', 'Still Present'),
        ('NOT_DETECTED', 'Not Detected'),
        ('POTENTIALLY_RELOCATED', 'Potentially Relocated'),
        ('POSSIBLE_MATCH', 'Possible Match'),
        ('REQUIRES_VERIFICATION', 'Requires Verification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    debris_object = models.ForeignKey(DebrisObject, on_delete=models.CASCADE, related_name='temporal_matches')
    previous_observation = models.ForeignKey(
        DetectionObservation, on_delete=models.CASCADE,
        related_name='as_previous'
    )
    candidate_observation = models.ForeignKey(
        DetectionObservation, on_delete=models.CASCADE,
        related_name='as_candidate', null=True, blank=True
    )
    distance_m = models.FloatField(null=True, blank=True)
    fingerprint_similarity = models.FloatField(null=True, blank=True,
                                                help_text='Fingerprint Similarity Score — not a probability')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='temporal_verifications'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_comment = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sonarx_temporal_matches'


class Verification(models.Model):
    DECISION_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('CLASS_CHANGED', 'Classification Changed'),
        ('ESCALATED', 'Escalated'),
        ('HAZARD_CONFIRMED', 'Hazard Confirmed'),
        ('HAZARD_DOWNGRADED', 'Hazard Downgraded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    detection = models.ForeignKey(Detection, on_delete=models.CASCADE, related_name='verifications')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='verifications'
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    new_class = models.CharField(max_length=25, blank=True)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sonarx_verifications'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.detection.detection_uid} | {self.decision} by {self.reviewer}"
