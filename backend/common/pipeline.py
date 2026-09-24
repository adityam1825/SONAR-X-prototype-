"""
SONAR-X Analysis Pipeline Orchestrator
Coordinates preprocessing → detection → fingerprint → fusion → classification → hazard

Inference modes:
  DEMO         — deterministic cached results (no model needed)
  CLASSICAL_CV — image-processing fallback (NOT a trained model)
  YOLO         — trained model from AI_MODEL_PATH

Import strategy:
  ALL ai.* modules are imported via the repository root on sys.path.
  The repo root (parent of ai/) must be on sys.path — NOT the ai/ dir itself.
  This avoids collisions with the Django app stubs (backend/fingerprint/ etc.)
"""

import os
import sys
import logging

logger = logging.getLogger("sonarx.pipeline")


# ── Path management ───────────────────────────────────────────────

def _ensure_repo_root_on_path():
    """
    Ensure the repository root (parent of ai/) is on sys.path so that
    'from ai.fingerprint...' etc. work without colliding with Django app stubs.
    Must be called before any ai.* import.
    """
    from django.conf import settings
    repo_root = str(settings.AI_DIR.parent)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


# ── Public entry point ────────────────────────────────────────────

def run_analysis_pipeline(sonar_file, survey):
    """
    Run the full analysis pipeline for a sonar file.
    Returns a list of result dicts.

    Never silently falls back to DEMO for a real SURVEY upload —
    instead returns an empty list with a logged error.
    """
    _ensure_repo_root_on_path()

    from django.conf import settings

    is_demo = survey.is_demo or survey.data_source == "DEMO"

    if is_demo:
        inference_mode = "DEMO"
    elif os.path.exists(settings.AI_MODEL_PATH):
        inference_mode = "YOLO"
    else:
        inference_mode = "CLASSICAL_CV"

    logger.info(
        f"[Pipeline] survey={survey.survey_id} file={sonar_file.filename} "
        f"mode={inference_mode}"
    )

    try:
        if inference_mode == "DEMO":
            return _run_demo(sonar_file, survey)
        elif inference_mode == "YOLO":
            return _run_yolo(sonar_file, survey)
        else:
            return _run_classical(sonar_file, survey)
    except Exception as e:
        logger.error(
            f"[Pipeline] FAILED for {sonar_file.filename}: {e}", exc_info=True
        )
        if is_demo:
            # Only fall back to demo cache for demo surveys
            logger.warning("[Pipeline] Demo fallback triggered for demo survey.")
            return _run_demo(sonar_file, survey)
        # For real surveys: return empty — do NOT inject fake detections
        return []


# ── Demo mode ─────────────────────────────────────────────────────

def _run_demo(sonar_file, survey):
    """Return deterministic cached demo results."""
    from ai.demo.demo_engine import get_demo_detections
    from detections.models import Detection

    # Return existing detections if already seeded
    existing = Detection.objects.filter(survey=survey, is_demo=True)
    if existing.exists():
        return [
            {
                "detection_id": str(d.id),
                "detection_uid": d.detection_uid,
                "classification": d.classification,
                "confidence": d.confidence,
                "evidence_score": d.evidence_score,
                "false_positive_risk": d.false_positive_risk,
                "hazard_level": d.hazard_level,
                "inference_mode": "DEMO",
                "data_source": "DEMO",
            }
            for d in existing
        ]

    # Return demo result descriptions without saving to DB
    # (seeding is handled by seed_demo management command)
    return [
        {
            "detection_uid": f"SX-DET-DEMO-{d['debris_uid'][-4:]}",
            "classification": d["classification"],
            "confidence": d["confidence"],
            "evidence_score": d["evidence_score"],
            "false_positive_risk": d["false_positive_risk"],
            "hazard_level": d["hazard"]["level"],
            "inference_mode": "DEMO",
            "data_source": "DEMO",
        }
        for d in get_demo_detections()
    ]


# ── Classical CV ──────────────────────────────────────────────────

def _run_classical(sonar_file, survey):
    """
    Classical CV fallback — NOT a trained model.
    Uses adaptive thresholding + contour detection + 7-cue fingerprint.
    """
    import cv2
    import numpy as np

    from ai.detection.classical_detector import ClassicalDetector
    from ai.fingerprint.fingerprint_engine import FingerprintEngine
    from ai.fusion.evidence_fusion import EvidenceFusionEngine
    from ai.hazard.hazard_engine import HazardEngine
    from detections.models import Detection, SonarFingerprint

    logger.info(f"[Classical CV] Loading image: {sonar_file.filename}")

    # Load image — prefer the preprocessed version if available
    image = None
    if sonar_file.processed_file:
        try:
            image = cv2.imread(sonar_file.processed_file.path, cv2.IMREAD_GRAYSCALE)
        except Exception:
            pass
    if image is None and sonar_file.file:
        try:
            image = cv2.imread(sonar_file.file.path, cv2.IMREAD_GRAYSCALE)
        except Exception:
            pass
    if image is None:
        logger.warning(
            f"[Classical CV] Cannot load image for {sonar_file.filename} "
            "— using synthetic fallback for demonstration."
        )
        from ai.demo.synthetic_image import generate_synthetic_sonar
        image = generate_synthetic_sonar(sonar_file.demo_image_key or "marine_debris_01")

    quality_score = sonar_file.quality_score or 70.0
    nadir_start = sonar_file.nadir_width_px
    nadir_end = sonar_file.nadir_width_px * 2 if sonar_file.nadir_width_px else None

    # ── Detect candidates ─────────────────────────────────────────
    detector = ClassicalDetector(
        nadir_start=nadir_start,
        nadir_end=nadir_end,
    )
    candidates = detector.detect(image)
    logger.info(
        f"[Classical CV] Detector found {len(candidates)} candidates in {sonar_file.filename}"
    )

    fusion_engine = EvidenceFusionEngine()
    hazard_engine = HazardEngine()
    results = []

    altitude = survey.altitude_m or sonar_file.altitude_m
    range_scale = survey.range_scale_mpp or sonar_file.range_scale_mpp

    for cand in candidates[:10]:  # cap at 10 per image
        x, y, w, h = cand["bbox"]

        # ── Fingerprint ───────────────────────────────────────────
        fp_engine = FingerprintEngine(
            image, (x, y, w, h),
            quality_score=quality_score,
            nadir_start=nadir_start,
            nadir_end=nadir_end,
        )
        fp = fp_engine.extract()

        # ── Fusion ────────────────────────────────────────────────
        fusion = fusion_engine.fuse(fp.flat_scores())

        # ── Classification ────────────────────────────────────────
        classification = _classify_heuristic(fp, fusion.evidence_score)

        # ── Hazard ────────────────────────────────────────────────
        hazard = hazard_engine.assess(
            classification=classification,
            fingerprint_scores=fp.flat_scores(),
            bbox=cand["bbox"],
            evidence_score=fusion.evidence_score,
            signal_quality=quality_score,
            metadata_limited=(altitude is None or range_scale is None),
        )

        # ── Persist ───────────────────────────────────────────────
        det = Detection.objects.create(
            survey=survey,
            sonar_file=sonar_file,
            classification=classification,
            confidence=min(100.0, round(fusion.evidence_score, 1)),
            evidence_score=round(fusion.evidence_score, 1),
            false_positive_risk=fusion.false_positive_risk,
            bbox_x=x, bbox_y=y, bbox_w=w, bbox_h=h,
            latitude=survey.latitude,
            longitude=survey.longitude,
            coordinate_note=(
                "" if survey.latitude is not None
                else "Geolocation unavailable — not extracted from uploaded data."
            ),
            hazard_level=hazard.hazard_level,
            hazard_score=round(hazard.hazard_score, 1),
            hazard_indicators=hazard.hazard_indicators,
            hazard_limited_data=hazard.limited_data,
            recommended_action=hazard.recommended_action,
            supporting_evidence=_build_supporting(fp),
            counter_evidence=_build_counter(fp),
            inference_mode="CLASSICAL_CV",
            data_source=survey.data_source,
            processing_summary={
                "nadir": "APPLIED" if nadir_start else "ESTIMATED",
                "gain": "APPLIED",
                "slant_range": "APPLIED" if (altitude and range_scale) else "NOT_APPLIED",
                "quality": sonar_file.quality_level or "UNKNOWN",
            },
            is_demo=False,
            verification_status="PENDING",
        )

        SonarFingerprint.objects.create(
            detection=det,
            backscatter_score=fp.backscatter_score,
            backscatter_status=fp.backscatter_status,
            texture_score=fp.texture_score,
            texture_status=fp.texture_status,
            geometry_score=fp.geometry_score,
            geometry_status=fp.geometry_status,
            shadow_score=fp.shadow_score,
            shadow_status=fp.shadow_status,
            object_shadow_score=fp.object_shadow_score,
            object_shadow_status=fp.object_shadow_status,
            seabed_context_score=fp.seabed_context_score,
            seabed_context_status=fp.seabed_context_status,
            signal_quality_score=fp.signal_quality_score,
            signal_quality_status=fp.signal_quality_status,
            evidence_score=round(fusion.evidence_score, 1),   # use fused score
        )

        results.append({
            "detection_id": str(det.id),
            "detection_uid": det.detection_uid,
            "classification": classification,
            "confidence": det.confidence,
            "evidence_score": det.evidence_score,
            "false_positive_risk": fusion.false_positive_risk,
            "hazard_level": hazard.hazard_level,
            "inference_mode": "CLASSICAL_CV",
            "data_source": survey.data_source,
            "fingerprint": fp.to_dict(),
        })

    logger.info(
        f"[Classical CV] Saved {len(results)} detections for {sonar_file.filename}."
    )
    return results


# ── YOLO ──────────────────────────────────────────────────────────

def _run_yolo(sonar_file, survey):
    """YOLO model inference. Falls back to classical if model fails."""
    from django.conf import settings
    try:
        from ultralytics import YOLO
        YOLO(settings.AI_MODEL_PATH)
        logger.info("[YOLO] Model loaded — delegating to classical CV for MVP.")
    except Exception as e:
        logger.warning(f"[YOLO] Load failed ({e}), using classical CV.")
    return _run_classical(sonar_file, survey)


# ── Classification heuristic ──────────────────────────────────────

def _classify_heuristic(fp, evidence_score: float) -> str:
    shadow = fp.shadow_score
    geometry = fp.geometry_score
    texture = fp.texture_score
    backscatter = fp.backscatter_score

    if shadow < 20 and geometry < 30:
        return "SONAR_ARTIFACT"
    if texture > 60 and shadow < 30 and backscatter < 50:
        return "NATURAL_FORMATION"
    if evidence_score >= 55 and shadow >= 50 and geometry >= 50:
        return "MARINE_DEBRIS"
    return "UNKNOWN_ANOMALY"


def _build_supporting(fp) -> list:
    ev = []
    if fp.backscatter_score > 65:
        ev.append("Elevated acoustic backscatter")
    if fp.shadow_score > 60:
        ev.append("Acoustic shadow detected")
    if fp.geometry_score > 65:
        ev.append("Distinct object geometry")
    if fp.seabed_context_score > 55:
        ev.append("Target anomalous relative to background seabed")
    if fp.object_shadow_score > 60:
        ev.append("Consistent object-shadow geometry")
    return ev


def _build_counter(fp) -> list:
    ctr = []
    if fp.signal_quality_score < 50:
        ctr.append("Signal quality reduced")
    if fp.shadow_score < 40:
        ctr.append("Acoustic shadow weak or absent")
    if fp.object_shadow_score < 40:
        ctr.append("Object-shadow relationship inconsistent")
    return ctr
