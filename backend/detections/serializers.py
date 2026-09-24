"""SONAR-X Detection Serializers"""

from rest_framework import serializers
from .models import Detection, SonarFingerprint, DebrisObject, DetectionObservation, TemporalMatch, Verification


class SonarFingerprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = SonarFingerprint
        exclude = ['detection']


class VerificationSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.SerializerMethodField()

    class Meta:
        model = Verification
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'reviewer']

    def get_reviewer_email(self, obj):
        return obj.reviewer.email if obj.reviewer else None


class DetectionSerializer(serializers.ModelSerializer):
    fingerprint = SonarFingerprintSerializer(read_only=True)
    verifications = VerificationSerializer(many=True, read_only=True)
    survey_name = serializers.SerializerMethodField()
    sonar_file_name = serializers.SerializerMethodField()

    class Meta:
        model = Detection
        fields = '__all__'

    def get_survey_name(self, obj):
        return obj.survey.name if obj.survey else None

    def get_sonar_file_name(self, obj):
        return obj.sonar_file.filename if obj.sonar_file else None


class DetectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    class Meta:
        model = Detection
        fields = [
            'id', 'detection_uid', 'survey_id', 'classification',
            'confidence', 'evidence_score', 'false_positive_risk',
            'hazard_level', 'verification_status', 'latitude', 'longitude',
            'debris_uid', 'temporal_status', 'data_source', 'inference_mode',
            'created_at',
        ]


class TemporalMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporalMatch
        fields = '__all__'


class DebrisObjectSerializer(serializers.ModelSerializer):
    observations = serializers.SerializerMethodField()

    class Meta:
        model = DebrisObject
        fields = '__all__'

    def get_observations(self, obj):
        obs = obj.observations.select_related('survey', 'detection').order_by('timestamp')
        return [
            {
                'id': str(o.id),
                'survey_id': o.survey.survey_id,
                'survey_name': o.survey.name,
                'detection_id': str(o.detection.id) if o.detection else None,
                'latitude': o.latitude,
                'longitude': o.longitude,
                'timestamp': o.timestamp.isoformat(),
                'classification': o.classification,
                'confidence': o.confidence,
                'hazard_level': o.hazard_level,
                'fingerprint': o.fingerprint_snapshot,
            }
            for o in obs
        ]
