"""
Unit tests for Sonar Preprocessing Engine.
"""
import sys, os
_ROOT = os.path.join(os.path.dirname(__file__), '..')
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
import numpy as np
import pytest
from ai.preprocessing.sonar_preprocessor import SonarPreprocessor


def make_test_image(h=256, w=512, seed=42):
    rng = np.random.default_rng(seed)
    img = rng.normal(60, 20, (h, w))
    # Nadir
    img[:, 236:276] = 5
    # Bright target
    img[80:110, 120:165] = 200
    return np.clip(img, 0, 255).astype(np.uint8)


class TestNadirDetection:
    def test_nadir_is_detected(self):
        img = make_test_image()
        p = SonarPreprocessor()
        result = p.run(img)
        assert result.nadir_start is not None
        assert result.nadir_end is not None
        assert result.nadir_end > result.nadir_start

    def test_nadir_override_used(self):
        img = make_test_image()
        p = SonarPreprocessor(nadir_override=(230, 280))
        result = p.run(img)
        assert result.nadir_start == 230
        assert result.nadir_end == 280
        assert result.nadir_status == 'APPLIED'
        assert result.nadir_method == 'OVERRIDE'

    def test_original_not_modified(self):
        img = make_test_image()
        original_copy = img.copy()
        p = SonarPreprocessor()
        result = p.run(img)
        # Original stored in result must match the input
        assert np.array_equal(result.original, original_copy)


class TestGainCorrection:
    def test_gain_applied_when_not_precorrected(self):
        img = make_test_image()
        p = SonarPreprocessor(already_gain_corrected=False)
        result = p.run(img)
        assert result.gain_status == 'APPLIED'

    def test_gain_skipped_when_precorrected(self):
        img = make_test_image()
        p = SonarPreprocessor(already_gain_corrected=True)
        result = p.run(img)
        assert result.gain_status == 'SKIPPED'


class TestSlantRangeCorrection:
    def test_slant_range_applied_with_metadata(self):
        img = make_test_image()
        p = SonarPreprocessor(altitude_m=2.5, range_scale_mpp=0.2)
        result = p.run(img)
        assert result.slant_range_status in ('APPLIED', 'NOT_APPLIED')

    def test_slant_range_skipped_without_altitude(self):
        img = make_test_image()
        p = SonarPreprocessor(altitude_m=None, range_scale_mpp=0.2)
        result = p.run(img)
        assert result.slant_range_status == 'NOT_APPLIED'
        assert 'altitude' in result.slant_range_reason.lower()

    def test_slant_range_skipped_without_range_scale(self):
        img = make_test_image()
        p = SonarPreprocessor(altitude_m=2.5, range_scale_mpp=None)
        result = p.run(img)
        assert result.slant_range_status == 'NOT_APPLIED'


class TestQualityAssessment:
    def test_quality_score_range(self):
        img = make_test_image()
        p = SonarPreprocessor()
        result = p.run(img)
        assert 0 <= result.quality_score <= 100

    def test_quality_level_valid(self):
        img = make_test_image()
        p = SonarPreprocessor()
        result = p.run(img)
        assert result.quality_level in ('GOOD', 'MODERATE', 'POOR')

    def test_low_quality_image(self):
        img = np.zeros((256, 512), dtype=np.uint8)
        p = SonarPreprocessor()
        result = p.run(img)
        assert result.quality_level in ('MODERATE', 'POOR')

