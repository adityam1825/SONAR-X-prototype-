"""Unit tests for Evidence Fusion Engine.
Uses ai.fusion.evidence_fusion to avoid Django app stub collision.
"""
import sys, os
_ROOT = os.path.join(os.path.dirname(__file__), '..')
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest
from ai.fusion.evidence_fusion import EvidenceFusionEngine


class TestEvidenceFusion:
    def test_high_scores_low_risk(self):
        engine = EvidenceFusionEngine()
        scores = {
            'backscatter': 90, 'texture': 85, 'geometry': 90,
            'shadow': 88, 'object_shadow': 82, 'seabed_context': 78, 'signal_quality': 92,
        }
        result = engine.fuse(scores)
        assert result.evidence_score > 70
        assert result.false_positive_risk == 'LOW'

    def test_low_scores_high_risk(self):
        engine = EvidenceFusionEngine()
        scores = {k: 15 for k in ['backscatter', 'texture', 'geometry', 'shadow',
                                   'object_shadow', 'seabed_context', 'signal_quality']}
        result = engine.fuse(scores)
        assert result.evidence_score < 40
        assert result.false_positive_risk == 'HIGH'

    def test_weights_normalize(self):
        engine = EvidenceFusionEngine({'a': 2, 'b': 3, 'c': 5})
        assert sum(engine.weights.values()) == pytest.approx(1.0, rel=1e-6)

    def test_zero_scores_give_zero_evidence(self):
        engine = EvidenceFusionEngine()
        scores = {k: 0 for k in ['backscatter', 'texture', 'geometry', 'shadow',
                                   'object_shadow', 'seabed_context', 'signal_quality']}
        result = engine.fuse(scores)
        assert result.evidence_score == pytest.approx(0.0)

    def test_note_mentions_not_validated(self):
        engine = EvidenceFusionEngine()
        result = engine.fuse({'backscatter': 50, 'texture': 50, 'geometry': 50,
                               'shadow': 50, 'object_shadow': 50, 'seabed_context': 50,
                               'signal_quality': 50})
        assert 'not' in result.note.lower() or 'demo' in result.note.lower()
