"""SONAR-X Detection Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Detection, SonarFingerprint, DebrisObject, DetectionObservation, TemporalMatch, Verification
from .serializers import (
    DetectionSerializer, DetectionListSerializer,
    VerificationSerializer, TemporalMatchSerializer, DebrisObjectSerializer
)


class DetectionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Detection.objects.all().select_related('survey', 'sonar_file').prefetch_related(
        'fingerprint', 'verifications'
    )

    def get_serializer_class(self):
        if self.action == 'list':
            return DetectionListSerializer
        return DetectionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        survey_id = self.request.query_params.get('survey')
        if survey_id:
            qs = qs.filter(survey__id=survey_id)
        classification = self.request.query_params.get('classification')
        if classification:
            qs = qs.filter(classification=classification)
        hazard = self.request.query_params.get('hazard')
        if hazard:
            qs = qs.filter(hazard_level=hazard)
        return qs

    @action(detail=True, methods=['get'])
    def hazard(self, request, pk=None):
        detection = self.get_object()
        return Response({
            'detection_uid': detection.detection_uid,
            'hazard_level': detection.hazard_level,
            'hazard_score': detection.hazard_score,
            'hazard_indicators': detection.hazard_indicators,
            'hazard_limited_data': detection.hazard_limited_data,
            'recommended_action': detection.recommended_action,
            'classification': detection.classification,
            'confidence': detection.confidence,
        })

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        detection = self.get_object()
        decision = request.data.get('decision')
        comment = request.data.get('comment', '')
        new_class = request.data.get('new_class', '')

        valid_decisions = ['CONFIRMED', 'REJECTED', 'CLASS_CHANGED', 'ESCALATED',
                           'HAZARD_CONFIRMED', 'HAZARD_DOWNGRADED']
        if decision not in valid_decisions:
            return Response({'error': f'Invalid decision. Must be one of {valid_decisions}'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Hazard downgrade requires a comment
        if decision == 'HAZARD_DOWNGRADED' and not comment:
            return Response({'error': 'A comment is required when downgrading hazard level.'},
                            status=status.HTTP_400_BAD_REQUEST)

        verification = Verification.objects.create(
            detection=detection,
            reviewer=request.user,
            decision=decision,
            comment=comment,
            new_class=new_class,
        )

        # Update detection verification status
        detection.verification_status = decision if decision in ['CONFIRMED', 'REJECTED', 'ESCALATED'] else 'CLASS_CHANGED'
        if decision == 'CLASS_CHANGED' and new_class:
            detection.reviewer_class = new_class

        if decision == 'HAZARD_DOWNGRADED':
            detection.hazard_level = 'NONE'

        detection.save()

        return Response(VerificationSerializer(verification).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        detection = self.get_object()
        verifications = detection.verifications.all()
        return Response({
            'detection_uid': detection.detection_uid,
            'verifications': VerificationSerializer(verifications, many=True).data,
        })

    @action(detail=True, methods=['get'])
    def temporal_analysis(self, request, pk=None):
        detection = self.get_object()
        if not detection.debris_uid:
            return Response({'message': 'No debris tracking ID for this detection.'})

        try:
            debris = DebrisObject.objects.get(debris_uid=detection.debris_uid)
        except DebrisObject.DoesNotExist:
            return Response({'message': f'Debris object {detection.debris_uid} not found.'})

        serializer = DebrisObjectSerializer(debris)
        return Response(serializer.data)


class DebrisObjectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = DebrisObject.objects.all()
    serializer_class = DebrisObjectSerializer

    @action(detail=True, methods=['post'])
    def verify_temporal(self, request, pk=None):
        debris = self.get_object()
        decision = request.data.get('decision')
        comment = request.data.get('comment', '')

        if decision not in ['CONFIRMED', 'REJECTED']:
            return Response({'error': "Decision must be CONFIRMED or REJECTED"}, status=400)

        latest_match = TemporalMatch.objects.filter(debris_object=debris).order_by('-created_at').first()
        if not latest_match:
            return Response({'error': 'No temporal match found for this debris object.'}, status=404)

        latest_match.verified_by = request.user
        latest_match.verified_at = timezone.now()
        latest_match.verification_comment = comment

        if decision == 'CONFIRMED':
            latest_match.status = 'POTENTIALLY_RELOCATED'
            debris.current_status = 'POTENTIALLY_RELOCATED'
        else:
            latest_match.status = 'NOT_DETECTED'
            debris.current_status = 'NOT_DETECTED'

        latest_match.save()
        debris.save()

        return Response({
            'debris_uid': debris.debris_uid,
            'status': debris.current_status,
            'message': f'Temporal case verified as {decision}.',
        })
