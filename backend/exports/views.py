"""SONAR-X Export Views â€” GeoJSON, KML, CSV"""

import csv
import json
import logging
from io import StringIO, BytesIO
from datetime import datetime, timezone

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from surveys.models import Survey
from detections.models import Detection

logger = logging.getLogger('sonarx.exports')

SOFTWARE_VERSION = getattr(settings, 'SONARX_VERSION', '0.1.0-prototype')


def _get_detections(survey, filters=None):
    """Get detections for export, applying optional filters."""
    qs = Detection.objects.filter(survey=survey)
    if filters:
        if filters.get('classification'):
            qs = qs.filter(classification=filters['classification'])
        if filters.get('min_confidence'):
            qs = qs.filter(confidence__gte=float(filters['min_confidence']))
        if filters.get('hazard_level'):
            qs = qs.filter(hazard_level=filters['hazard_level'])
    return qs


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_geojson(request, survey_id):
    """Export detections as GeoJSON (RFC 7946, WGS84)."""
    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        return Response({'error': 'Survey not found.'}, status=404)

    detections = _get_detections(survey, request.query_params)
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'

    features = []
    excluded = 0

    for det in detections:
        if det.latitude is None or det.longitude is None:
            excluded += 1
            continue

        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [det.longitude, det.latitude],  # RFC 7946: lon, lat
            },
            'properties': {
                'debris_id': det.debris_uid or det.detection_uid,
                'detection_uid': det.detection_uid,
                'class': det.classification,
                'confidence': det.confidence,
                'evidence_score': det.evidence_score,
                'false_positive_risk': det.false_positive_risk,
                'hazard_level': det.hazard_level,
                'verification_status': det.verification_status,
                'survey_id': survey.survey_id,
                'timestamp': det.created_at.isoformat(),
                'temporal_status': det.temporal_status,
                'data_source': det.data_source,
                'inference_mode': det.inference_mode,
            },
        }
        features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'properties': {
            'data_source': survey.data_source,
            'software_version': SOFTWARE_VERSION,
            'survey_id': survey.survey_id,
            'generation_timestamp': now,
            'processing_summary': f'{len(features)} geolocated detections exported.',
            'excluded_no_coords': excluded,
            'verification_disclaimer': (
                'AI-generated observations require human verification. '
                'Export includes prototype evidence scores, NOT validated probabilities.'
            ),
            'crs': 'WGS84',
        },
    }

    response = HttpResponse(
        json.dumps(geojson, indent=2),
        content_type='application/geo+json',
    )
    response['Content-Disposition'] = f'attachment; filename="sonarx_{survey.survey_id}.geojson"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_kml(request, survey_id):
    """Export detections as KML."""
    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        return Response({'error': 'Survey not found.'}, status=404)

    detections = _get_detections(survey, request.query_params)
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'

    try:
        import simplekml
        kml = simplekml.Kml()
        kml.document.name = f"SONAR-X Export: {survey.name}"
        kml.document.description = (
            f"Data Source: {survey.data_source}\n"
            f"Survey: {survey.survey_id}\n"
            f"Generated: {now}\n"
            f"Software: {SOFTWARE_VERSION}\n"
            f"DISCLAIMER: AI-generated observations require human verification."
        )

        # Define styles
        styles = {
            'HIGH_CAUTION': simplekml.Style(),
            'CAUTION': simplekml.Style(),
            'NONE': simplekml.Style(),
        }
        styles['HIGH_CAUTION'].iconstyle.color = simplekml.Color.red
        styles['HIGH_CAUTION'].iconstyle.scale = 1.5
        styles['CAUTION'].iconstyle.color = simplekml.Color.yellow
        styles['CAUTION'].iconstyle.scale = 1.2
        styles['NONE'].iconstyle.color = simplekml.Color.blue

        excluded = 0
        for det in detections:
            if det.latitude is None or det.longitude is None:
                excluded += 1
                continue

            pnt = kml.newpoint(
                name=det.detection_uid,
                coords=[(det.longitude, det.latitude)],
            )
            pnt.description = (
                f"Class: {det.classification}\n"
                f"Confidence (prototype): {det.confidence:.0f}\n"
                f"Evidence Score: {det.evidence_score:.0f}\n"
                f"False Positive Risk: {det.false_positive_risk}\n"
                f"Hazard Level: {det.hazard_level}\n"
                f"Verification: {det.verification_status}\n"
                f"Data Source: {det.data_source}\n"
                f"Inference Mode: {det.inference_mode}\n"
                f"Timestamp: {det.created_at.isoformat()}"
            )

            style_key = det.hazard_level if det.hazard_level in styles else 'NONE'
            pnt.style = styles[style_key]

        kml_str = kml.kml()

    except ImportError:
        # Manual KML generation if simplekml not available
        placemarks = []
        for det in detections:
            if det.latitude is None or det.longitude is None:
                continue
            placemarks.append(
                f"""  <Placemark>
    <name>{det.detection_uid}</name>
    <description><![CDATA[
      Class: {det.classification}
      Hazard: {det.hazard_level}
      Data Source: {det.data_source}
    ]]></description>
    <Point><coordinates>{det.longitude},{det.latitude},0</coordinates></Point>
  </Placemark>"""
            )

        kml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>SONAR-X Export: {survey.name}</name>
  {''.join(placemarks)}
</Document>
</kml>"""

    response = HttpResponse(kml_str, content_type='application/vnd.google-earth.kml+xml')
    response['Content-Disposition'] = f'attachment; filename="sonarx_{survey.survey_id}.kml"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv(request, survey_id):
    """Export all detections as CSV (including those without coordinates)."""
    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        return Response({'error': 'Survey not found.'}, status=404)

    detections = _get_detections(survey, request.query_params)
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'

    output = StringIO()
    writer = csv.writer(output)

    # Header comments (not formula-injectable)
    writer.writerow(['# SONAR-X Export'])
    writer.writerow([f'# Data Source: {survey.data_source}'])
    writer.writerow([f'# Survey: {survey.survey_id}'])
    writer.writerow([f'# Generated: {now}'])
    writer.writerow([f'# Software: {SOFTWARE_VERSION}'])
    writer.writerow(['# DISCLAIMER: AI-generated â€” requires human verification'])
    writer.writerow([])

    # Column headers
    writer.writerow([
        'detection_uid', 'debris_uid', 'classification', 'confidence_prototype_score',
        'evidence_score', 'false_positive_risk', 'hazard_level',
        'latitude', 'longitude', 'coordinate_note',
        'verification_status', 'temporal_status',
        'survey_id', 'data_source', 'inference_mode', 'timestamp',
    ])

    for det in detections:
        # CSV formula injection protection: strip leading = + - @ from strings
        def safe_str(val):
            if val is None:
                return ''
            s = str(val)
            if s and s[0] in '=+-@':
                s = "'" + s
            return s

        writer.writerow([
            safe_str(det.detection_uid),
            safe_str(det.debris_uid),
            safe_str(det.classification),
            safe_str(det.confidence),
            safe_str(det.evidence_score),
            safe_str(det.false_positive_risk),
            safe_str(det.hazard_level),
            det.latitude if det.latitude is not None else '',
            det.longitude if det.longitude is not None else '',
            safe_str(det.coordinate_note or ('Geolocation unavailable' if det.latitude is None else '')),
            safe_str(det.verification_status),
            safe_str(det.temporal_status),
            safe_str(survey.survey_id),
            safe_str(det.data_source),
            safe_str(det.inference_mode),
            det.created_at.isoformat(),
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sonarx_{survey.survey_id}.csv"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_summary(request, survey_id):
    """Return export summary (counts by class, hazard, etc.)."""
    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        return Response({'error': 'Survey not found.'}, status=404)

    detections = Detection.objects.filter(survey=survey)
    geolocated = detections.filter(latitude__isnull=False, longitude__isnull=False).count()

    return Response({
        'survey_id': survey.survey_id,
        'total_detections': detections.count(),
        'geolocated': geolocated,
        'no_coordinates': detections.count() - geolocated,
        'by_class': {
            'marine_debris': detections.filter(classification='MARINE_DEBRIS').count(),
            'natural_formation': detections.filter(classification='NATURAL_FORMATION').count(),
            'sonar_artifact': detections.filter(classification='SONAR_ARTIFACT').count(),
            'unknown_anomaly': detections.filter(classification='UNKNOWN_ANOMALY').count(),
        },
        'by_hazard': {
            'none': detections.filter(hazard_level='NONE').count(),
            'caution': detections.filter(hazard_level='CAUTION').count(),
            'high_caution': detections.filter(hazard_level='HIGH_CAUTION').count(),
        },
        'data_source': survey.data_source,
    })

