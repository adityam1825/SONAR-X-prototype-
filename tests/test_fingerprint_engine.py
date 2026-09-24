"""Unit tests for SonarFingerprint engine.
Imports via ai.fingerprint.fingerprint_engine to avoid collision
with the backend/fingerprint Django app stub.
"""
import sys, os
# Ensure ai/ is importable via the 'ai' package prefix
_ROOT = os.path.join(os.path.dirname(__file__), '..')
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np
import pytest
from ai.fingerprint.fingerprint_engine import FingerprintEngine, _score_to_status


def make_image(h=256, w=512, value=80, seed=42):
    rng = np.random.default_rng(seed)
    img = np.clip(rng.normal(value, 20, (h, w)), 0, 255).astype(np.uint8)
    return img


class TestFingerprintEngine:
    def test_basic_extraction(self):
        img = make_image()
        img[80:110, 120:165] = 220
        engine = FingerprintEngine(img, bbox=(120, 80, 45, 30), quality_score=85.0)
        result = engine.extract()
        assert 0 <= result.backscatter_score <= 100
        assert 0 <= result.texture_score <= 100
        assert 0 <= result.geometry_score <= 100
        assert 0 <= result.shadow_score <= 100
        assert 0 <= result.object_shadow_score <= 100
        assert 0 <= result.seabed_context_score <= 100
        assert result.signal_quality_score == pytest.approx(85.0)

    def test_empty_target_returns_zero(self):
        img = make_image()
        engine = FingerprintEngine(img, bbox=(600, 300, 10, 10), quality_score=70.0)
        result = engine.extract()
        assert result.backscatter_score == 0.0

    def test_high_backscatter_target(self):
        img = np.ones((256, 512), dtype=np.uint8) * 40
        img[100:130, 150:200] = 240
        engine = FingerprintEngine(img, bbox=(150, 100, 50, 30), quality_score=90.0)
        result = engine.extract()
        assert result.backscatter_score > 50

    def test_nadir_exclusion_no_crash(self):
        img = make_image()
        engine = FingerprintEngine(img, bbox=(120, 80, 45, 30),
                                   quality_score=85.0, nadir_start=230, nadir_end=280)
        result = engine.extract()
        assert result.geometry_score >= 0

    def test_status_thresholds(self):
        assert _score_to_status(85) == 'STRONG'
        assert _score_to_status(55) == 'MODERATE'
        assert _score_to_status(20) == 'WEAK'
        assert _score_to_status(0) == 'UNAVAILABLE'
