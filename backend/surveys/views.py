"""SONAR-X Survey Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Survey
from .serializers import SurveySerializer, SurveyListSerializer


class SurveyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Survey.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return SurveyListSerializer
        return SurveySerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def demo(self, request):
        """Return demo surveys."""
        surveys = Survey.objects.filter(is_demo=True).order_by('-created_at')
        serializer = SurveyListSerializer(surveys, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Dashboard statistics."""
        from detections.models import Detection
        total_surveys = Survey.objects.count()
        total_detections = Detection.objects.count()
        debris_count = Detection.objects.filter(classification='MARINE_DEBRIS').count()
        natural_count = Detection.objects.filter(classification='NATURAL_FORMATION').count()
        artifact_count = Detection.objects.filter(classification='SONAR_ARTIFACT').count()
        unknown_count = Detection.objects.filter(classification='UNKNOWN_ANOMALY').count()
        hazard_count = Detection.objects.exclude(hazard_level='NONE').count()
        pending_verification = Detection.objects.filter(verification_status='PENDING').count()

        return Response({
            'total_surveys': total_surveys,
            'total_detections': total_detections,
            'marine_debris': debris_count,
            'natural_formation': natural_count,
            'sonar_artifact': artifact_count,
            'unknown_anomaly': unknown_count,
            'hazard_flags': hazard_count,
            'pending_verification': pending_verification,
        })

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger analysis pipeline for a survey."""
        survey = self.get_object()
        from sonar.models import SonarFile
        from common.pipeline import run_analysis_pipeline

        files = SonarFile.objects.filter(survey=survey)
        if not files.exists():
            return Response(
                {'error': 'No sonar files uploaded for this survey.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        for f in files:
            result = run_analysis_pipeline(f, survey)
            results.append(result)

        survey.status = 'COMPLETED'
        survey.save()

        return Response({'results': results, 'survey_id': survey.survey_id})

    @action(detail=True, methods=['post'])
    def follow_up(self, request, pk=None):
        """Create a follow-up survey linked to this one."""
        original = self.get_object()
        data = request.data.copy()
        data['name'] = data.get('name', f"Follow-up: {original.name}")
        data['is_demo'] = original.is_demo

        serializer = SurveySerializer(data=data, context={'request': request})
        if serializer.is_valid():
            follow_up = serializer.save(created_by=request.user)
            return Response(SurveySerializer(follow_up).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
