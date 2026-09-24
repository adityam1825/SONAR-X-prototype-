"""SONAR-X Evaluation Models"""

from django.db import models
from django.conf import settings
import uuid


class EvaluationDataset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    source = models.CharField(max_length=200)
    split = models.CharField(max_length=20, default='test')
    image_count = models.IntegerField(default=0)
    object_count = models.IntegerField(default=0)
    class_distribution = models.JSONField(default=dict)
    synthetic = models.BooleanField(default=True)
    citation = models.TextField(blank=True)
    license = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sonarx_eval_datasets'

    def __str__(self):
        return f"{self.name} ({'synthetic' if self.synthetic else 'real'})"


class EvaluationRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(EvaluationDataset, on_delete=models.CASCADE, related_name='runs')
    model_version = models.CharField(max_length=50)
    configuration_version = models.CharField(max_length=50)
    inference_mode = models.CharField(max_length=15)
    timestamp = models.DateTimeField(auto_now_add=True)
    # Detection metrics
    metrics = models.JSONField(default=dict, help_text='Overall metrics dict')
    per_class_metrics = models.JSONField(default=dict)
    confusion_matrix = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    # Integrity flags
    train_test_overlap_checked = models.BooleanField(default=False)
    test_split_used_for_tuning = models.BooleanField(default=False)
    small_sample_warning = models.BooleanField(default=False)

    class Meta:
        db_table = 'sonarx_eval_runs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Eval Run {self.id} | {self.model_version} | {self.timestamp.date()}"
