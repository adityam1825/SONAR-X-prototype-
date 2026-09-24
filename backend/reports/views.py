"""SONAR-X Report Generation Views"""

import sys
import logging
from io import BytesIO
from django.conf import settings
from django.http import FileResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from surveys.models import Survey
from detections.models import Detection, DebrisObject
from .models import Report

logger = logging.getLogger('sonarx.reports')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_survey_report(request, survey_id):
    """Generate a PDF survey report."""
    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        return Response({'error': 'Survey not found.'}, status=404)

    sys.path.insert(0, str(settings.AI_DIR.parent))

    try:
        from ai.report_generator import SurveyReportGenerator
        detections = Detection.objects.filter(survey=survey).select_related('survey')
        generator = SurveyReportGenerator(survey, list(detections))
        pdf_buffer = generator.generate()

        from django.core.files.base import ContentFile
        report = Report.objects.create(
            survey=survey,
            report_type='SURVEY',
            generated_by=request.user,
        )
        report.file.save(
            f"survey_report_{survey.survey_id}.pdf",
            ContentFile(pdf_buffer.getvalue()),
        )
        report.save()

        return Response({
            'report_id': str(report.id),
            'download_url': request.build_absolute_uri(report.file.url),
            'survey_id': survey.survey_id,
        })
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        return Response({'error': f'Report generation failed: {str(e)}'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_temporal_report(request, debris_uid):
    """Generate a temporal intelligence PDF report."""
    try:
        debris = DebrisObject.objects.get(debris_uid=debris_uid)
    except DebrisObject.DoesNotExist:
        return Response({'error': f'Debris object {debris_uid} not found.'}, status=404)

    sys.path.insert(0, str(settings.AI_DIR.parent))

    try:
        from ai.report_generator import TemporalReportGenerator
        generator = TemporalReportGenerator(debris)
        pdf_buffer = generator.generate()

        from django.core.files.base import ContentFile
        report = Report.objects.create(
            report_type='TEMPORAL',
            generated_by=request.user,
        )
        report.file.save(
            f"temporal_report_{debris_uid}.pdf",
            ContentFile(pdf_buffer.getvalue()),
        )
        report.save()

        return Response({
            'report_id': str(report.id),
            'download_url': request.build_absolute_uri(report.file.url),
            'debris_uid': debris_uid,
        })
    except Exception as e:
        logger.error(f"Temporal report generation failed: {e}", exc_info=True)
        return Response({'error': f'Report generation failed: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_report(request, report_id):
    """Download a generated report PDF."""
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return Response({'error': 'Report not found.'}, status=404)

    if not report.file:
        return Response({'error': 'Report file not found.'}, status=404)

    return FileResponse(
        report.file.open('rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=f"sonarx_report_{report.id}.pdf",
    )

