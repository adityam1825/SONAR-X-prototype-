"""
SONAR-X Automatic Ingest Endpoint
POST /api/surveys/ingest/

The user's ONLY required action is to upload a sonar image.
SONAR-X automatically performs the entire analysis pipeline.

Import strategy:
  All ai.* modules are imported after the repository root is on sys.path.
  Repository root = parent of ai/ = settings.AI_DIR.parent
"""

import os
import sys
import logging
import datetime
import tempfile

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status

logger = logging.getLogger("sonarx.ingest")

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif"}
MAX_BYTES = getattr(settings, "MAX_UPLOAD_SIZE_MB", 100) * 1024 * 1024


def _add_repo_root():
    """Add the repository root to sys.path so 'from ai.*' imports work."""
    repo_root = str(settings.AI_DIR.parent)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


# ── Main endpoint ─────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def ingest_survey(request):
    """
    Upload-only entry point. Accepts one or more sonar image files.
    Performs: validate → metadata → survey → preprocess → detect →
              fingerprint → fuse → classify → hazard → report.
    Returns: complete survey + detection results.
    """
    _add_repo_root()

    # ── Collect and validate uploaded files ───────────────────────
    uploaded_files = request.FILES.getlist("files") or (
        [request.FILES["file"]] if "file" in request.FILES else []
    )
    if not uploaded_files:
        return Response(
            {"error": "No file provided. Please upload a sonar image."},
            status=http_status.HTTP_400_BAD_REQUEST,
        )

    for f in uploaded_files:
        _, ext = os.path.splitext(f.name.lower())
        if ext not in ALLOWED_EXTENSIONS:
            return Response(
                {"error": f'Unsupported file type "{ext}". Supported: PNG, JPG, JPEG, TIFF.'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        if f.size > MAX_BYTES:
            return Response(
                {"error": f"File too large ({f.size/1024/1024:.1f} MB). Max: {settings.MAX_UPLOAD_SIZE_MB} MB."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

    # ── Extract metadata from first file ──────────────────────────
    primary_file = uploaded_files[0]
    meta = _extract_metadata(primary_file)

    # ── Build survey fields ───────────────────────────────────────
    survey_name = (meta.survey_name.value if meta and meta.survey_name.value
                   else _auto_name(primary_file.name))
    try:
        survey_date = (datetime.date.fromisoformat(meta.survey_date.value)
                       if meta and meta.survey_date.value
                       else datetime.date.today())
    except Exception:
        survey_date = datetime.date.today()

    lat = meta.latitude.value if meta else None
    lon = meta.longitude.value if meta else None
    altitude = meta.altitude_m.value if meta else None
    range_scale = meta.range_scale_mpp.value if meta else None
    channel = (meta.channel_layout.value or "BOTH") if meta else "BOTH"
    channel = channel if channel in ("PORT", "STARBOARD", "BOTH") else "BOTH"

    # ── Create Survey ─────────────────────────────────────────────
    from surveys.models import Survey
    survey = Survey.objects.create(
        name=survey_name,
        date=survey_date,
        area=meta.survey_area.value if meta and meta.survey_area.value else "",
        operator=meta.operator.value if meta and meta.operator.value else "",
        created_by=request.user,
        data_source="SURVEY",
        status="UPLOADING",
        latitude=lat,
        longitude=lon,
        altitude_m=altitude,
        range_scale_mpp=range_scale,
        channel_layout=channel,
        already_gain_corrected=False,
        already_slant_range_corrected=False,
        already_processed=False,
        notes=_build_notes(meta),
        is_demo=False,
    )
    logger.info(f"[Ingest] Survey created: {survey.survey_id}")

    # ── Save sonar files ──────────────────────────────────────────
    from sonar.models import SonarFile, ProcessingLog
    sonar_files = []
    for uf in uploaded_files:
        sf = SonarFile.objects.create(
            survey=survey,
            file=uf,
            filename=uf.name,
            file_type=os.path.splitext(uf.name)[1].lstrip(".").upper(),
            file_size_bytes=uf.size,
            data_source="SURVEY",
            is_demo=False,
            status="UPLOADED",
        )
        # Populate dimensions
        try:
            from PIL import Image as PILImage
            img_pil = PILImage.open(sf.file.path)
            sf.width, sf.height = img_pil.width, img_pil.height
            sf.is_grayscale = img_pil.mode in ("L", "LA")
            img_pil.close()
            sf.save()
        except Exception as e:
            logger.warning(f"[Ingest] PIL dimension read failed: {e}")
        sonar_files.append(sf)

    # ── Validate ──────────────────────────────────────────────────
    survey.status = "VALIDATING"
    survey.save()
    validation_results = []
    for sf in sonar_files:
        vr = _quick_validate(sf)
        validation_results.append(vr)
        if vr["result"] == "INVALID":
            survey.status = "FAILED"
            survey.save()
            return Response(
                {"error": f"File {sf.filename} failed validation: {'; '.join(vr['errors'])}"},
                status=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
    logger.info(f"[Ingest] Validation passed for {len(sonar_files)} file(s)")

    # ── Preprocess ────────────────────────────────────────────────
    survey.status = "PREPROCESSING"
    survey.save()
    preprocessing_summary = {}
    for sf in sonar_files:
        try:
            ps = _auto_preprocess(sf, survey)
            preprocessing_summary[str(sf.id)] = ps
            logger.info(f"[Ingest] Preprocessing done: {sf.filename}")
        except Exception as e:
            logger.warning(f"[Ingest] Preprocessing failed for {sf.filename}: {e}", exc_info=True)
            preprocessing_summary[str(sf.id)] = {"status": "FAILED", "reason": str(e)}

    # ── Analysis pipeline ─────────────────────────────────────────
    survey.status = "ANALYZING"
    survey.save()
    from common.pipeline import run_analysis_pipeline
    all_results = []
    for sf in sonar_files:
        try:
            r = run_analysis_pipeline(sf, survey)
            all_results.extend(r if isinstance(r, list) else [r])
        except Exception as e:
            logger.error(f"[Ingest] Pipeline failed for {sf.filename}: {e}", exc_info=True)
    logger.info(f"[Ingest] Pipeline produced {len(all_results)} detection(s)")

    # ── Complete ──────────────────────────────────────────────────
    survey.status = "COMPLETED"
    survey.save()

    # ── Auto-generate PDF report ──────────────────────────────────
    report_info = _auto_generate_report(survey, request)

    # ── Build response ────────────────────────────────────────────
    from detections.models import Detection
    detections_qs = Detection.objects.filter(survey=survey)

    return Response(
        {
            "survey_id": survey.survey_id,
            "survey_pk": survey.id,
            "survey_name": survey.name,
            "survey_date": str(survey.date),
            "status": "COMPLETED",
            "inference_mode": _infer_mode(all_results),
            "data_source": "SURVEY",
            "metadata_summary": _meta_summary(meta),
            "validation": validation_results,
            "preprocessing": preprocessing_summary,
            "detection_count": detections_qs.count(),
            "detections": [
                {
                    "id": str(d.id),
                    "detection_uid": d.detection_uid,
                    "classification": d.classification,
                    "confidence": d.confidence,
                    "evidence_score": d.evidence_score,
                    "false_positive_risk": d.false_positive_risk,
                    "hazard_level": d.hazard_level,
                    "inference_mode": d.inference_mode,
                }
                for d in detections_qs
            ],
            "report": report_info,
            "survey_url": f"/surveys/{survey.id}/results",
        },
        status=http_status.HTTP_201_CREATED,
    )


# ── Helpers ───────────────────────────────────────────────────────

def _extract_metadata(uploaded_file):
    """Save to temp, run metadata extraction, return result."""
    _, ext = os.path.splitext(uploaded_file.name)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as t:
            for chunk in uploaded_file.chunks():
                t.write(chunk)
            tmp = t.name
        uploaded_file.seek(0)  # reset for later save

        from ai.metadata_extractor import SonarMetadataExtractor
        extractor = SonarMetadataExtractor(
            file_path=tmp,
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
        )
        return extractor.extract()
    except Exception as e:
        logger.error(f"[Metadata] Extraction failed: {e}", exc_info=True)
        return None
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except Exception:
                pass


def _auto_preprocess(sf, survey) -> dict:
    """Run the sonar preprocessing pipeline on sf. Returns step status dict."""
    import cv2
    from ai.preprocessing.sonar_preprocessor import SonarPreprocessor
    from sonar.models import ProcessingLog
    from django.core.files.base import ContentFile

    img = None
    if sf.file:
        try:
            img = cv2.imread(sf.file.path, cv2.IMREAD_GRAYSCALE)
        except Exception:
            pass
    if img is None:
        return {"status": "SKIPPED", "reason": "Cannot load image from disk"}

    preprocessor = SonarPreprocessor(
        altitude_m=survey.altitude_m,
        range_scale_mpp=survey.range_scale_mpp,
        already_gain_corrected=survey.already_gain_corrected,
        already_slant_range_corrected=survey.already_slant_range_corrected,
    )
    result = preprocessor.run(img)

    # Save processed image
    _, buf = cv2.imencode(".png", result.processed)
    sf.processed_file.save(
        f"processed_{sf.filename}.png",
        ContentFile(buf.tobytes()),
        save=False,
    )
    sf.quality_score = result.quality_score
    sf.quality_level = result.quality_level
    sf.saturation_ratio = result.saturation_ratio
    sf.dropout_ratio = result.dropout_ratio
    sf.snr_proxy = result.snr_proxy
    sf.nadir_width_px = result.nadir_width_px
    sf.image_contrast = result.image_contrast
    sf.usable_area_ratio = result.usable_area_ratio
    sf.pixel_scale_gpp = result.pixel_scale_gpp
    sf.status = "PREPROCESSED"
    sf.save()

    # Processing logs
    step_map = [
        ("NADIR",       "nadir_status",       "nadir_reason"),
        ("GAIN",        "gain_status",        "gain_reason"),
        ("SLANT_RANGE", "slant_range_status", "slant_range_reason"),
        ("NOISE",       "noise_status",       None),
        ("CONTRAST",    "contrast_status",    None),
        ("QUALITY",     "quality_status",     None),
    ]
    for step_key, status_attr, reason_attr in step_map:
        ProcessingLog.objects.create(
            file=sf,
            step=step_key,
            status=getattr(result, status_attr, "SKIPPED"),
            reason=getattr(result, reason_attr, "") if reason_attr else "",
            software_version=getattr(settings, "SONARX_VERSION", "0.1.0-prototype"),
        )

    return result.to_dict()


def _quick_validate(sf) -> dict:
    """Validate an uploaded sonar file. Returns status dict."""
    import cv2
    import numpy as np
    checks, warnings, errors = [], [], []

    if not (sf.file and os.path.exists(sf.file.path)):
        errors.append("File not found on disk after upload")
        return {"result": "INVALID", "checks": checks, "warnings": warnings, "errors": errors}

    checks.append({"name": "File accessible", "status": "PASS"})

    try:
        img = cv2.imread(sf.file.path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            errors.append("Cannot decode image data")
            return {"result": "INVALID", "checks": checks, "warnings": warnings, "errors": errors}

        h, w = img.shape
        checks.append({"name": "Image readable", "status": "PASS", "value": f"{w}x{h}"})

        if w >= 64 and h >= 64:
            checks.append({"name": "Dimensions", "status": "PASS", "value": f"{w}x{h}"})
        else:
            warnings.append(f"Very small image: {w}x{h}")
            checks.append({"name": "Dimensions", "status": "WARN"})

        std_val = float(np.std(img))
        if std_val > 5:
            checks.append({"name": "Signal", "status": "PASS", "value": f"std={std_val:.1f}"})
        else:
            warnings.append("Near-uniform image — very low signal content")
            checks.append({"name": "Signal", "status": "WARN"})

        sf.width, sf.height, sf.is_grayscale = w, h, True
        sf.save()

    except Exception as e:
        errors.append(f"Validation error: {e}")
        return {"result": "INVALID", "checks": checks, "warnings": warnings, "errors": errors}

    result = "INVALID" if errors else ("WARNING" if warnings else "VALID")
    return {"result": result, "checks": checks, "warnings": warnings, "errors": errors}


def _auto_generate_report(survey, request) -> dict:
    """Generate a PDF survey report automatically. Returns info dict."""
    try:
        from ai.report_generator import SurveyReportGenerator
        from detections.models import Detection
        from reports.models import Report
        from django.core.files.base import ContentFile

        detections = list(Detection.objects.filter(survey=survey))
        pdf_buf = SurveyReportGenerator(survey, detections).generate()

        report = Report.objects.create(
            survey=survey, report_type="SURVEY", generated_by=request.user
        )
        report.file.save(
            f"auto_{survey.survey_id}.pdf", ContentFile(pdf_buf.getvalue())
        )
        report.save()
        return {
            "report_id": str(report.id),
            "download_url": request.build_absolute_uri(report.file.url),
            "status": "GENERATED",
        }
    except Exception as e:
        logger.warning(f"[Ingest] Report failed: {e}", exc_info=True)
        return {"status": "FAILED", "reason": str(e)}


def _auto_name(filename: str) -> str:
    import re
    stem = os.path.splitext(filename)[0]
    clean = re.sub(r"[_\-\.]+", " ", stem).strip()
    date_str = datetime.date.today().strftime("%d %b %Y")
    return f"SONAR Survey — {clean} — {date_str}" if clean else f"SONAR Survey — {date_str}"


def _build_notes(meta) -> str:
    if not meta:
        return "Auto-ingested survey. No embedded metadata available."
    parts = ["Auto-ingested. Metadata extracted automatically."]
    if meta.latitude.status == "NOT_AVAILABLE":
        parts.append("GPS unavailable.")
    if meta.altitude_m.status == "NOT_AVAILABLE":
        parts.append("Altitude unavailable — slant-range correction skipped.")
    if meta.range_scale_mpp.status == "NOT_AVAILABLE":
        parts.append("Range scale unavailable.")
    return " ".join(parts)


def _meta_summary(meta) -> dict:
    if not meta:
        return {"status": "NO_METADATA", "message": "No metadata could be extracted."}
    found, missing = [], []
    for label, ok in [
        ("GPS Coordinates",   meta.latitude.status != "NOT_AVAILABLE"),
        ("Acquisition Date",  meta.survey_date.status in ("VERIFIED", "ESTIMATED")),
        ("Sensor Model",      meta.sensor_model.status != "NOT_AVAILABLE"),
        ("Altitude",          meta.altitude_m.status != "NOT_AVAILABLE"),
        ("Range Scale",       meta.range_scale_mpp.status != "NOT_AVAILABLE"),
        ("Channel Layout",    meta.channel_layout.status != "NOT_AVAILABLE"),
        ("Image Dimensions",  meta.image_width.status != "NOT_AVAILABLE"),
    ]:
        (found if ok else missing).append(label)
    return {
        "found": found,
        "unavailable": missing,
        "note": (
            "All unavailable fields were not fabricated. "
            "SONAR-X continues processing without them where possible."
        ),
    }


def _infer_mode(results: list) -> str:
    if not results:
        return "CLASSICAL_CV"
    modes = {r.get("inference_mode", "CLASSICAL_CV") for r in results if isinstance(r, dict)}
    if "YOLO" in modes:        return "YOLO"
    if "CLASSICAL_CV" in modes: return "CLASSICAL_CV"
    return "DEMO"
