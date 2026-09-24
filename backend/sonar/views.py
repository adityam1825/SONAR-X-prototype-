"""SONAR-X Sonar File Views — Upload, Validation, Preprocessing"""

import os
import sys
import base64
import logging
from io import BytesIO

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SonarFile, ProcessingLog, ValidationResult
from surveys.models import Survey

logger = logging.getLogger('sonarx.sonar')

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif'}
MAX_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_file(request, survey_id):
    """Upload a sonar image file to a survey."""
    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        return Response({'error': 'Survey not found.'}, status=404)

    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({'error': 'No file provided.'}, status=400)

    # Validate extension
    _, ext = os.path.splitext(file_obj.name.lower())
    if ext not in ALLOWED_EXTENSIONS:
        return Response({
            'error': f'Unsupported file type "{ext}". Supported: PNG, JPG, JPEG, TIFF. '
                     f'Note: Raw XTF/JSF ingestion is future scope.'
        }, status=400)

    # Validate size
    if file_obj.size > MAX_SIZE_BYTES:
        return Response({
            'error': f'File too large ({file_obj.size / 1024 / 1024:.1f} MB). '
                     f'Maximum: {settings.MAX_UPLOAD_SIZE_MB} MB.'
        }, status=400)

    sonar_file = SonarFile.objects.create(
        survey=survey,
        file=file_obj,
        filename=file_obj.name,
        file_type=ext.lstrip('.').upper(),
        file_size_bytes=file_obj.size,
        data_source=survey.data_source,
        is_demo=(survey.data_source == 'DEMO'),
    )

    # Read image metadata
    try:
        from PIL import Image as PILImage
        img = PILImage.open(sonar_file.file.path)
        sonar_file.width = img.width
        sonar_file.height = img.height
        sonar_file.is_grayscale = img.mode in ('L', 'LA')
        sonar_file.save()
    except Exception as e:
        logger.warning(f"Could not read image dimensions: {e}")

    return Response({
        'id': str(sonar_file.id),
        'filename': sonar_file.filename,
        'file_size_bytes': sonar_file.file_size_bytes,
        'width': sonar_file.width,
        'height': sonar_file.height,
        'is_grayscale': sonar_file.is_grayscale,
        'survey_id': survey.survey_id,
        'data_source': sonar_file.data_source,
        'status': sonar_file.status,
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_file(request, file_id):
    """Run validation on an uploaded sonar file."""
    try:
        sonar_file = SonarFile.objects.get(id=file_id)
    except SonarFile.DoesNotExist:
        return Response({'error': 'File not found.'}, status=404)

    # Import inline to avoid circular imports
    sys.path.insert(0, str(settings.AI_DIR.parent))

    checks = []
    warnings = []
    errors = []

    # 1. File exists
    if sonar_file.file and os.path.exists(sonar_file.file.path):
        checks.append({'name': 'File exists', 'status': 'PASS'})
    elif sonar_file.is_demo:
        checks.append({'name': 'File exists', 'status': 'PASS', 'note': 'Demo file'})
    else:
        errors.append('File not found on disk.')
        checks.append({'name': 'File exists', 'status': 'FAIL'})

    # 2. File extension
    _, ext = os.path.splitext(sonar_file.filename.lower())
    if ext in ALLOWED_EXTENSIONS:
        checks.append({'name': 'File extension', 'status': 'PASS', 'value': ext})
    else:
        errors.append(f'Unsupported extension: {ext}')
        checks.append({'name': 'File extension', 'status': 'FAIL'})

    # 3. File size
    if sonar_file.file_size_bytes and 1024 <= sonar_file.file_size_bytes <= MAX_SIZE_BYTES:
        checks.append({'name': 'File size', 'status': 'PASS',
                       'value': f'{sonar_file.file_size_bytes / 1024:.1f} KB'})
    elif sonar_file.is_demo:
        checks.append({'name': 'File size', 'status': 'PASS', 'note': 'Demo'})
    else:
        warnings.append('File size unusual. May be empty or oversized.')
        checks.append({'name': 'File size', 'status': 'WARN'})

    # 4. Image readability
    sat_ratio = None
    dropout_ratio = None
    nadir_detected = None

    if sonar_file.file and os.path.exists(sonar_file.file.path):
        try:
            import cv2
            import numpy as np
            img = cv2.imread(sonar_file.file.path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                checks.append({'name': 'Image readable', 'status': 'PASS',
                               'value': f'{img.shape[1]}x{img.shape[0]}'})

                # 5. Dimensions
                h, w = img.shape
                sonar_file.width = w
                sonar_file.height = h
                if w >= 64 and h >= 64:
                    checks.append({'name': 'Dimensions', 'status': 'PASS', 'value': f'{w}x{h}'})
                else:
                    warnings.append('Image dimensions are very small.')
                    checks.append({'name': 'Dimensions', 'status': 'WARN', 'value': f'{w}x{h}'})

                # 6. Grayscale check
                sonar_file.is_grayscale = True
                checks.append({'name': 'Grayscale format', 'status': 'PASS'})

                # 7. Saturation check
                sat_ratio = float(np.sum((img <= 2) | (img >= 253))) / img.size
                sonar_file.saturation_ratio = sat_ratio
                if sat_ratio > 0.5:
                    warnings.append(f'High saturation ratio: {sat_ratio:.2%}')
                    checks.append({'name': 'Saturation', 'status': 'WARN', 'value': f'{sat_ratio:.2%}'})
                else:
                    checks.append({'name': 'Saturation', 'status': 'PASS', 'value': f'{sat_ratio:.2%}'})

                # 8. Dropout check
                row_means = np.mean(img, axis=1)
                dropout_rows = np.sum(row_means < 5)
                dropout_ratio = float(dropout_rows) / h
                sonar_file.dropout_ratio = dropout_ratio
                if dropout_ratio > 0.2:
                    warnings.append(f'High dropout ratio: {dropout_ratio:.2%}')
                    checks.append({'name': 'Dropout lines', 'status': 'WARN', 'value': f'{dropout_ratio:.2%}'})
                else:
                    checks.append({'name': 'Dropout lines', 'status': 'PASS', 'value': f'{dropout_ratio:.2%}'})

                # 9. Nadir region detection
                centre = w // 2
                centre_profile = np.mean(img[:, max(0, centre - w // 5):min(w, centre + w // 5)], axis=0)
                min_val = float(np.min(centre_profile))
                nadir_detected = min_val < 20
                checks.append({
                    'name': 'Nadir region',
                    'status': 'PASS' if nadir_detected else 'WARN',
                    'value': 'Detected' if nadir_detected else 'Not clearly detected',
                })

                # 10. Signal quality
                signal_std = float(np.std(img))
                if signal_std > 20:
                    checks.append({'name': 'Signal quality', 'status': 'PASS', 'value': f'std={signal_std:.1f}'})
                else:
                    warnings.append('Low signal variation — image may be uniformly dark.')
                    checks.append({'name': 'Signal quality', 'status': 'WARN', 'value': f'std={signal_std:.1f}'})

            else:
                errors.append('Could not decode image.')
                checks.append({'name': 'Image readable', 'status': 'FAIL'})
        except Exception as e:
            warnings.append(f'Image analysis error: {str(e)}')
            checks.append({'name': 'Image readable', 'status': 'WARN'})
    else:
        checks.append({'name': 'Image readable', 'status': 'SKIP', 'note': 'Demo mode'})

    # 11. Metadata
    survey = sonar_file.survey
    if survey.altitude_m is not None:
        checks.append({'name': 'Altitude metadata', 'status': 'PASS', 'value': f'{survey.altitude_m}m'})
    else:
        warnings.append('Altitude unavailable — slant-range correction will be skipped.')
        checks.append({'name': 'Altitude metadata', 'status': 'WARN', 'value': 'Unavailable'})

    if survey.range_scale_mpp is not None:
        checks.append({'name': 'Range scale metadata', 'status': 'PASS', 'value': f'{survey.range_scale_mpp}m/px'})
    else:
        warnings.append('Range scale unavailable — slant-range correction will be skipped.')
        checks.append({'name': 'Range scale metadata', 'status': 'WARN', 'value': 'Unavailable'})

    # Determine overall result
    if errors:
        overall = 'INVALID'
    elif warnings:
        overall = 'WARNING'
    else:
        overall = 'VALID'

    # Save validation result
    ValidationResult.objects.update_or_create(
        file=sonar_file,
        defaults={
            'result': overall,
            'checks': checks,
            'warnings': warnings,
            'errors': errors,
            'saturation_ratio': sat_ratio,
            'dropout_ratio': dropout_ratio,
            'nadir_detected': nadir_detected,
            'signal_quality': 'GOOD' if not warnings else 'MODERATE',
        }
    )

    # Update file status
    sonar_file.status = overall if overall != 'VALID' else 'VALID'
    sonar_file.save()

    # Log
    ProcessingLog.objects.create(
        file=sonar_file,
        step='VALIDATION',
        status='COMPLETE',
        output_summary={'result': overall, 'checks': len(checks), 'warnings': len(warnings), 'errors': len(errors)},
        software_version=settings.SONARX_VERSION,
    )

    return Response({
        'file_id': str(sonar_file.id),
        'filename': sonar_file.filename,
        'result': overall,
        'checks': checks,
        'warnings': warnings,
        'errors': errors,
        'metadata_status': {
            'altitude': survey.altitude_m is not None,
            'range_scale': survey.range_scale_mpp is not None,
            'channel_layout': survey.channel_layout,
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preprocess_file(request, file_id):
    """Run sonar preprocessing pipeline on a file."""
    try:
        sonar_file = SonarFile.objects.get(id=file_id)
    except SonarFile.DoesNotExist:
        return Response({'error': 'File not found.'}, status=404)

    sys.path.insert(0, str(settings.AI_DIR.parent))
    survey = sonar_file.survey

    # Load image
    image = None
    if sonar_file.file and os.path.exists(sonar_file.file.path):
        import cv2
        image = cv2.imread(sonar_file.file.path, cv2.IMREAD_GRAYSCALE)

    if image is None and not sonar_file.is_demo:
        return Response({'error': 'Cannot load image for preprocessing.'}, status=400)

    # For demo mode, generate synthetic sonar image
    if image is None and sonar_file.is_demo:
        from ai.demo.synthetic_image import generate_synthetic_sonar
        image = generate_synthetic_sonar(sonar_file.demo_image_key or 'marine_debris_01')
    # Read preprocessing params from request or survey
    nadir_override = None
    if request.data.get('nadir_start') and request.data.get('nadir_end'):
        nadir_override = (int(request.data['nadir_start']), int(request.data['nadir_end']))

    median_filter_size = int(request.data.get('median_filter_size', 3))
    clahe_clip_limit = float(request.data.get('clahe_clip_limit', 2.0))
    clahe_tile_size = int(request.data.get('clahe_tile_size', 8))

    from ai.preprocessing.sonar_preprocessor import SonarPreprocessor

    preprocessor = SonarPreprocessor(
        altitude_m=survey.altitude_m,
        range_scale_mpp=survey.range_scale_mpp,
        already_gain_corrected=survey.already_gain_corrected,
        already_slant_range_corrected=survey.already_slant_range_corrected,
        nadir_override=nadir_override,
        median_filter_size=median_filter_size,
        clahe_clip_limit=clahe_clip_limit,
        clahe_tile_size=clahe_tile_size,
    )

    try:
        result = preprocessor.run(image)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return Response({'error': f'Preprocessing failed: {str(e)}'}, status=500)

    # Save processed image
    import cv2
    import numpy as np
    from django.core.files.base import ContentFile

    _, buf = cv2.imencode('.png', result.processed)
    processed_content = ContentFile(buf.tobytes())
    sonar_file.processed_file.save(
        f"processed_{sonar_file.filename}.png",
        processed_content,
        save=False
    )
    sonar_file.quality_score = result.quality_score
    sonar_file.quality_level = result.quality_level
    sonar_file.saturation_ratio = result.saturation_ratio
    sonar_file.dropout_ratio = result.dropout_ratio
    sonar_file.snr_proxy = result.snr_proxy
    sonar_file.nadir_width_px = result.nadir_width_px
    sonar_file.image_contrast = result.image_contrast
    sonar_file.usable_area_ratio = result.usable_area_ratio
    sonar_file.pixel_scale_gpp = result.pixel_scale_gpp
    sonar_file.status = 'PREPROCESSED'
    sonar_file.save()

    # Log each step
    for step_name, field_name in [
        ('NADIR', 'nadir_status'), ('GAIN', 'gain_status'),
        ('SLANT_RANGE', 'slant_range_status'), ('NOISE', 'noise_status'),
        ('CONTRAST', 'contrast_status'), ('QUALITY', 'quality_status'),
    ]:
        step_status = getattr(result, field_name, 'SKIPPED')
        ProcessingLog.objects.create(
            file=sonar_file,
            step=step_name,
            status=step_status,
            reason=getattr(result, f'{field_name.replace("_status", "_reason")}', ''),
            output_summary=result.to_dict().get(field_name.replace('_status', '').lower(), {}),
            software_version=settings.SONARX_VERSION,
        )

    # Encode images as base64 for frontend preview
    _, orig_buf = cv2.imencode('.png', result.original)
    orig_b64 = base64.b64encode(orig_buf.tobytes()).decode()

    _, proc_buf = cv2.imencode('.png', result.processed)
    proc_b64 = base64.b64encode(proc_buf.tobytes()).decode()

    return Response({
        'file_id': str(sonar_file.id),
        'processing_result': result.to_dict(),
        'original_image_b64': orig_b64,
        'processed_image_b64': proc_b64,
        'across_track_profile': result.across_track_profile,
        'quality': {
            'score': result.quality_score,
            'level': result.quality_level,
            'flags': result.quality_flags,
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def processing_log(request, file_id):
    """Get processing log for a file."""
    try:
        sonar_file = SonarFile.objects.get(id=file_id)
    except SonarFile.DoesNotExist:
        return Response({'error': 'File not found.'}, status=404)

    logs = sonar_file.processing_logs.all().order_by('timestamp')
    return Response({
        'file_id': str(sonar_file.id),
        'filename': sonar_file.filename,
        'logs': [
            {
                'step': log.step,
                'status': log.status,
                'reason': log.reason,
                'output_summary': log.output_summary,
                'timestamp': log.timestamp.isoformat(),
                'software_version': log.software_version,
            }
            for log in logs
        ],
    })
