"""Unit tests for Temporal Matching Engine.
Uses ai.temporal.temporal_engine to avoid Django app stub collision.
"""
import sys, os
_ROOT = os.path.join(os.path.dirname(__file__), '..')
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest
from ai.temporal.temporal_engine import TemporalMatcher, fingerprint_similarity, haversine_distance

BASE_FP = {'backscatter': 82, 'texture': 71, 'geometry': 88,
           'shadow': 76, 'object_shadow': 81, 'seabed_context': 69, 'signal_quality': 91}


class TestTemporalMatcher:
    def test_no_candidates_not_detected(self):
        matcher = TemporalMatcher(search_radius_m=500, similarity_threshold=0.65)
        result = matcher.match(
            previous={'latitude': 19.4521, 'longitude': 72.8403,
                      'classification': 'MARINE_DEBRIS', 'fingerprint': BASE_FP},
            candidates=[],
        )
        assert result['status'] == 'NOT_DETECTED'
        notes = result['notes'].lower()
        assert 'does not confirm' in notes or 'does not prove' in notes or 'does not' in notes

    def test_nearby_similar_potentially_relocated(self):
        matcher = TemporalMatcher(search_radius_m=500, similarity_threshold=0.65)
        candidate_fp = {k: v - 5 for k, v in BASE_FP.items()}
        result = matcher.match(
            previous={'latitude': 19.4521, 'longitude': 72.8403,
                      'classification': 'MARINE_DEBRIS', 'fingerprint': BASE_FP},
            candidates=[{
                'latitude': 19.4535, 'longitude': 72.8421,
                'classification': 'MARINE_DEBRIS', 'fingerprint': candidate_fp
            }],
        )
        assert result['status'] in ('STILL_PRESENT', 'POTENTIALLY_RELOCATED', 'POSSIBLE_MATCH')

    def test_no_gps_requires_verification(self):
        matcher = TemporalMatcher()
        result = matcher.match(
            previous={'latitude': None, 'longitude': None,
                      'classification': 'MARINE_DEBRIS', 'fingerprint': BASE_FP},
            candidates=[{'latitude': 19.45, 'longitude': 72.84,
                         'classification': 'MARINE_DEBRIS', 'fingerprint': BASE_FP}],
        )
        assert result['status'] == 'REQUIRES_VERIFICATION'

    def test_fingerprint_similarity_cosine(self):
        assert fingerprint_similarity(BASE_FP, BASE_FP) == pytest.approx(1.0, abs=0.001)
        zero_fp = {k: 0 for k in BASE_FP}
        assert fingerprint_similarity(BASE_FP, zero_fp) == 0.0

    def test_haversine_local(self):
        d = haversine_distance(19.4521, 72.8403, 19.4535, 72.8421)
        assert 180 < d < 300

    def test_not_detected_no_movement_claim(self):
        matcher = TemporalMatcher(search_radius_m=100)
        result = matcher.match(
            previous={'latitude': 19.45, 'longitude': 72.84,
                      'classification': 'MARINE_DEBRIS', 'fingerprint': BASE_FP},
            candidates=[{'latitude': 20.0, 'longitude': 73.5,
                         'classification': 'MARINE_DEBRIS', 'fingerprint': BASE_FP}],
        )
        assert result['status'] == 'NOT_DETECTED'
        notes = result['notes'].lower()
        if 'moved' in notes:
            assert 'not' in notes or 'does not' in notes
