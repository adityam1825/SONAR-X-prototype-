"""SONAR-X Temporal Intelligence Views"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from detections.models import DebrisObject, TemporalMatch, DetectionObservation
from detections.serializers import DebrisObjectSerializer, TemporalMatchSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def temporal_overview(request):
    """Overview of all tracked debris objects."""
    debris_objects = DebrisObject.objects.all().order_by('-first_observed')
    serializer = DebrisObjectSerializer(debris_objects, many=True)
    return Response({
        'count': debris_objects.count(),
        'debris_objects': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def temporal_detail(request, debris_uid):
    """Detailed temporal analysis for a tracked debris object."""
    try:
        debris = DebrisObject.objects.get(debris_uid=debris_uid)
    except DebrisObject.DoesNotExist:
        return Response({'error': f'Debris object {debris_uid} not found.'}, status=404)

    serializer = DebrisObjectSerializer(debris)
    matches = TemporalMatch.objects.filter(debris_object=debris).order_by('-created_at')
    match_data = TemporalMatchSerializer(matches, many=True).data

    return Response({
        'debris_object': serializer.data,
        'temporal_matches': match_data,
    })
