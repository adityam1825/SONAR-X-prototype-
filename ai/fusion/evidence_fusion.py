"""
SONAR-X Evidence Fusion Engine

Fuses seven sonar fingerprint cues into:
- Evidence Score (0–100)
- False Positive Risk (LOW / MEDIUM / HIGH)
- Classification confidence

IMPORTANT:
Weights are configurable demonstration values.
They are NOT scientifically validated coefficients.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import logging

logger = logging.getLogger('sonarx.fusion')


# Default configurable weights
DEFAULT_WEIGHTS = {
    'backscatter': 0.15,
    'texture': 0.15,
    'geometry': 0.15,
    'shadow': 0.20,
    'object_shadow': 0.15,
    'seabed_context': 0.10,
    'signal_quality': 0.10,
}

CONFIGURATION_VERSION = '0.1-demo'


@dataclass
class FusionResult:
    evidence_score: float = 0.0
    false_positive_risk: str = 'HIGH'
    weights_used: Dict[str, float] = field(default_factory=dict)
    weighted_contributions: Dict[str, float] = field(default_factory=dict)
    configuration_version: str = CONFIGURATION_VERSION
    note: str = (
        'Evidence fusion weights are configurable demonstration values. '
        'They are NOT scientifically validated coefficients.'
    )

    def to_dict(self):
        return {
            'evidence_score': round(self.evidence_score, 1),
            'false_positive_risk': self.false_positive_risk,
            'weights_used': {k: round(v, 4) for k, v in self.weights_used.items()},
            'weighted_contributions': {k: round(v, 2) for k, v in self.weighted_contributions.items()},
            'configuration_version': self.configuration_version,
            'note': self.note,
        }


class EvidenceFusionEngine:
    """
    Weighted evidence fusion for sonar fingerprint cues.

    Parameters
    ----------
    weights : dict, optional
        Custom weight dict. Keys must match fingerprint cue names.
        Weights will be normalized to sum to 1.0.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        raw_weights = weights or DEFAULT_WEIGHTS.copy()
        total = sum(raw_weights.values())
        if total <= 0:
            raise ValueError("Weights must sum to a positive value.")
        self.weights = {k: v / total for k, v in raw_weights.items()}

    def fuse(self, scores: Dict[str, float]) -> FusionResult:
        """
        Fuse fingerprint scores into evidence score.

        Parameters
        ----------
        scores : dict
            {'backscatter': float, 'texture': float, ...} — values 0–100

        Returns
        -------
        FusionResult
        """
        result = FusionResult(weights_used=self.weights.copy())

        evidence = 0.0
        contributions = {}
        for cue, weight in self.weights.items():
            score = scores.get(cue, 0.0)
            contribution = weight * score
            evidence += contribution
            contributions[cue] = contribution

        result.evidence_score = min(100.0, max(0.0, evidence))
        result.weighted_contributions = contributions
        result.false_positive_risk = self._compute_risk(result.evidence_score, scores)

        return result

    def _compute_risk(self, evidence_score: float, scores: Dict[str, float]) -> str:
        """
        Compute false-positive risk from evidence score and individual cues.

        Strong shadow + good geometry + high backscatter → LOW risk.
        Weak cues across the board → HIGH risk.
        """
        signal_quality = scores.get('signal_quality', 0.0)
        shadow = scores.get('shadow', 0.0)
        geometry = scores.get('geometry', 0.0)

        # Penalise for poor signal quality
        if signal_quality < 30:
            evidence_score = evidence_score * 0.7

        if evidence_score >= 70 and shadow >= 50 and geometry >= 50:
            return 'LOW'
        elif evidence_score >= 45 or (shadow >= 40 and geometry >= 40):
            return 'MEDIUM'
        else:
            return 'HIGH'
