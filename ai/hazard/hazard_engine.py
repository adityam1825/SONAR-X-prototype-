"""
SONAR-X Precautionary Hazard Assessment Engine

IMPORTANT SCIENTIFIC CONSTRAINTS:
- This engine NEVER identifies specific hazardous objects.
- It NEVER says "This is a mine", "This is a bomb", or "This is a wreck".
- It only says "Potential Hazard — Do Not Disturb" when sonar evidence warrants human review.
- Absence of a hazard flag does NOT mean an object is safe.
- Hazard assessment is PRECAUTIONARY only.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging

logger = logging.getLogger('sonarx.hazard')


@dataclass
class HazardResult:
    hazard_level: str = 'NONE'       # NONE / CAUTION / HIGH_CAUTION
    hazard_score: float = 0.0        # 0–100
    hazard_indicators: List[str] = field(default_factory=list)
    recommended_action: str = ''
    limited_data: bool = False
    banner_text: Optional[str] = None
    note: str = (
        '"Potential Hazard — Do Not Disturb" means sonar evidence warrants human review. '
        'This system does NOT identify specific hazardous objects. '
        'Absence of a hazard flag does NOT mean an object is safe.'
    )

    def to_dict(self):
        return {
            'hazard_level': self.hazard_level,
            'hazard_score': round(self.hazard_score, 1),
            'hazard_indicators': self.hazard_indicators,
            'recommended_action': self.recommended_action,
            'limited_data': self.limited_data,
            'banner_text': self.banner_text,
            'note': self.note,
        }


class HazardEngine:
    """
    Rule-based precautionary hazard assessment.

    Parameters
    ----------
    large_extent_threshold : int
        Bounding box area threshold (pixels²) for "large extent".
    """

    def __init__(self, large_extent_threshold: int = 5000):
        self.large_extent_threshold = large_extent_threshold

    def assess(
        self,
        classification: str,
        fingerprint_scores: Dict[str, float],
        bbox: tuple,
        evidence_score: float,
        signal_quality: float,
        metadata_limited: bool = False,
    ) -> HazardResult:
        """
        Assess hazard level for a detection.

        Parameters
        ----------
        classification : str
            One of MARINE_DEBRIS / NATURAL_FORMATION / SONAR_ARTIFACT / UNKNOWN_ANOMALY
        fingerprint_scores : dict
            Seven-cue scores (0–100 each)
        bbox : tuple
            (x, y, w, h) in pixels
        evidence_score : float
            Fused evidence score
        signal_quality : float
            Signal quality score from preprocessing
        metadata_limited : bool
            True if metadata was missing or incomplete

        Returns
        -------
        HazardResult
        """
        result = HazardResult()
        indicators = []
        score = 0.0

        x, y, bw, bh = bbox
        area = bw * bh

        # Natural formations are low hazard unless anomalous
        if classification == 'NATURAL_FORMATION':
            result.hazard_level = 'NONE'
            result.recommended_action = 'Standard survey documentation.'
            return result

        # Sonar artifacts are low hazard
        if classification == 'SONAR_ARTIFACT':
            result.hazard_level = 'NONE'
            result.recommended_action = 'Review sonar acquisition parameters.'
            return result

        # --- Indicator checks ---

        # 1. Large extent
        if area >= self.large_extent_threshold:
            indicators.append('Large spatial extent')
            score += 25

        # 2. Structured / regular geometry
        geometry_score = fingerprint_scores.get('geometry', 0.0)
        if geometry_score >= 70:
            indicators.append('Regular / structured geometry')
            score += 20

        # 3. Strong backscatter
        backscatter = fingerprint_scores.get('backscatter', 0.0)
        if backscatter >= 75:
            indicators.append('Strong acoustic backscatter')
            score += 15

        # 4. Prominent acoustic shadow
        shadow = fingerprint_scores.get('shadow', 0.0)
        if shadow >= 70:
            indicators.append('Prominent acoustic shadow')
            score += 15

        # 5. Unknown class with anomalous evidence
        if classification == 'UNKNOWN_ANOMALY' and evidence_score >= 55:
            indicators.append('Unknown class with strong acoustic evidence')
            score += 20

        # 6. Limited metadata or poor signal quality
        if metadata_limited or signal_quality < 40:
            indicators.append('Limited metadata / reduced signal quality')
            score += 10
            result.limited_data = True

        result.hazard_score = min(100.0, score)
        result.hazard_indicators = indicators

        # --- Level assignment ---
        num_indicators = len(indicators)

        # Rule: large + unknown → minimum CAUTION
        if area >= self.large_extent_threshold and classification == 'UNKNOWN_ANOMALY':
            score = max(score, 40)

        # Rule: large + structured geometry → minimum CAUTION
        if area >= self.large_extent_threshold and geometry_score >= 65:
            score = max(score, 40)

        if score >= 60 or num_indicators >= 3:
            result.hazard_level = 'HIGH_CAUTION'
            result.banner_text = 'POTENTIAL HAZARD — DO NOT DISTURB'
            result.recommended_action = (
                'Do not disturb. Human expert review required before any '
                'intervention. Maintain safe standoff distance.'
            )
        elif score >= 30 or num_indicators >= 1:
            result.hazard_level = 'CAUTION'
            result.recommended_action = (
                'Human verification required. Treat with caution pending expert review.'
            )
        else:
            result.hazard_level = 'NONE'
            result.recommended_action = 'Standard survey documentation.'

        result.hazard_score = score
        return result
