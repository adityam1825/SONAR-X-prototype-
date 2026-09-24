"""Unit tests for Hazard Engine.
Uses ai.hazard.hazard_engine to avoid Django app stub collision.
"""
import sys, os, re
_ROOT = os.path.join(os.path.dirname(__file__), '..')
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest
from ai.hazard.hazard_engine import HazardEngine


class TestHazardEngine:
    def test_natural_formation_no_hazard(self):
        engine = HazardEngine()
        result = engine.assess(
            classification='NATURAL_FORMATION',
            fingerprint_scores={'backscatter': 50, 'texture': 60, 'geometry': 40,
                                 'shadow': 30, 'object_shadow': 35,
                                 'seabed_context': 25, 'signal_quality': 80},
            bbox=(100, 80, 40, 30), evidence_score=45, signal_quality=80,
        )
        assert result.hazard_level == 'NONE'

    def test_sonar_artifact_no_hazard(self):
        engine = HazardEngine()
        result = engine.assess(
            classification='SONAR_ARTIFACT',
            fingerprint_scores={k: 20 for k in ['backscatter','texture','geometry',
                                                  'shadow','object_shadow','seabed_context','signal_quality']},
            bbox=(0, 200, 512, 5), evidence_score=20, signal_quality=70,
        )
        assert result.hazard_level == 'NONE'

    def test_large_unknown_caution(self):
        engine = HazardEngine(large_extent_threshold=1000)
        result = engine.assess(
            classification='UNKNOWN_ANOMALY',
            fingerprint_scores={'backscatter': 80, 'texture': 70, 'geometry': 75,
                                 'shadow': 80, 'object_shadow': 75,
                                 'seabed_context': 70, 'signal_quality': 85},
            bbox=(100, 80, 100, 80), evidence_score=70, signal_quality=85,
        )
        assert result.hazard_level in ('CAUTION', 'HIGH_CAUTION')

    def test_never_identifies_specific_object(self):
        engine = HazardEngine()
        result = engine.assess(
            classification='UNKNOWN_ANOMALY',
            fingerprint_scores={k: 85 for k in ['backscatter','texture','geometry',
                                                  'shadow','object_shadow','seabed_context','signal_quality']},
            bbox=(100, 80, 100, 80), evidence_score=80, signal_quality=85,
        )
        combined = (
            result.recommended_action.lower() + ' ' +
            ' '.join(result.hazard_indicators).lower() + ' ' +
            result.note.lower()
        )
        for forbidden in ['mine', 'bomb', 'munition', 'wreck', 'explosive', 'ied']:
            assert not re.search(r'\b' + forbidden + r'\b', combined), \
                f"Found forbidden term '{forbidden}' as standalone word in hazard output"

    def test_limited_data_flag(self):
        engine = HazardEngine()
        result = engine.assess(
            classification='MARINE_DEBRIS',
            fingerprint_scores={k: 50 for k in ['backscatter','texture','geometry',
                                                  'shadow','object_shadow','seabed_context','signal_quality']},
            bbox=(100, 80, 40, 30), evidence_score=50, signal_quality=20,
            metadata_limited=True,
        )
        assert result.limited_data is True
