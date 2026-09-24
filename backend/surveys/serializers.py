"""SONAR-X Survey Serializers"""

from rest_framework import serializers
from .models import Survey


class SurveySerializer(serializers.ModelSerializer):
    detection_count = serializers.ReadOnlyField()
    created_by_email = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = '__all__'
        read_only_fields = ['survey_id', 'created_at', 'updated_at', 'created_by']

    def get_created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else None

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class SurveyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    detection_count = serializers.ReadOnlyField()

    class Meta:
        model = Survey
        fields = [
            'id', 'survey_id', 'name', 'date', 'area', 'operator',
            'data_source', 'status', 'is_demo', 'detection_count',
            'created_at', 'latitude', 'longitude',
        ]
