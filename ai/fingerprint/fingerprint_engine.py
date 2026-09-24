"""
SONAR-X Seven-Cue Sonar Fingerprint Engine

Cues:
1. Backscatter / Intensity
2. Texture
3. Geometry
4. Acoustic Shadow
5. Object-Shadow Relationship
6. Seabed Context
7. Signal Quality

Each cue returns a score (0–100) and a status (STRONG / MODERATE / WEAK / UNAVAILABLE).
"""

import numpy as np
import cv2
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger('sonarx.fingerprint')


def _score_to_status(score: float) -> str:
    if score >= 70:
        return 'STRONG'
    elif score >= 40:
        return 'MODERATE'
    elif score > 0:
        return 'WEAK'
    else:
        return 'UNAVAILABLE'


@dataclass
class FingerprintResult:
    backscatter_score: float = 0.0
    backscatter_status: str = 'UNAVAILABLE'

    texture_score: float = 0.0
    texture_status: str = 'UNAVAILABLE'

    geometry_score: float = 0.0
    geometry_status: str = 'UNAVAILABLE'

    shadow_score: float = 0.0
    shadow_status: str = 'UNAVAILABLE'

    object_shadow_score: float = 0.0
    object_shadow_status: str = 'UNAVAILABLE'

    seabed_context_score: float = 0.0
    seabed_context_status: str = 'UNAVAILABLE'

    signal_quality_score: float = 0.0
    signal_quality_status: str = 'UNAVAILABLE'

    evidence_score: float = 0.0
    raw_features: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'backscatter': {'score': round(self.backscatter_score, 1), 'status': self.backscatter_status},
            'texture': {'score': round(self.texture_score, 1), 'status': self.texture_status},
            'geometry': {'score': round(self.geometry_score, 1), 'status': self.geometry_status},
            'shadow': {'score': round(self.shadow_score, 1), 'status': self.shadow_status},
            'object_shadow': {'score': round(self.object_shadow_score, 1), 'status': self.object_shadow_status},
            'seabed_context': {'score': round(self.seabed_context_score, 1), 'status': self.seabed_context_status},
            'signal_quality': {'score': round(self.signal_quality_score, 1), 'status': self.signal_quality_status},
            'evidence_score': round(self.evidence_score, 1),
        }

    def flat_scores(self) -> Dict[str, float]:
        return {
            'backscatter': self.backscatter_score,
            'texture': self.texture_score,
            'geometry': self.geometry_score,
            'shadow': self.shadow_score,
            'object_shadow': self.object_shadow_score,
            'seabed_context': self.seabed_context_score,
            'signal_quality': self.signal_quality_score,
        }


class FingerprintEngine:
    """
    Extracts the seven-cue sonar fingerprint for a detection candidate.

    Parameters
    ----------
    image : np.ndarray
        Preprocessed sonar image (grayscale, uint8).
    bbox : tuple
        Bounding box (x, y, w, h) in pixel coordinates.
    quality_score : float
        Quality score from preprocessing (0–100).
    nadir_start : int or None
        Left edge of nadir region (pixels).
    nadir_end : int or None
        Right edge of nadir region (pixels).
    """

    CONTEXT_PAD = 2  # multiplier for context region

    def __init__(
        self,
        image: np.ndarray,
        bbox: tuple,
        quality_score: float = 100.0,
        nadir_start: Optional[int] = None,
        nadir_end: Optional[int] = None,
    ):
        if len(image.shape) == 3:
            self.image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            self.image = image.astype(np.uint8)

        self.h, self.w = self.image.shape
        self.bbox = bbox  # (x, y, w, h)
        self.quality_score = quality_score
        self.nadir_start = nadir_start
        self.nadir_end = nadir_end

        x, y, bw, bh = bbox
        # Clamp to image bounds
        self.x1 = max(0, int(x))
        self.y1 = max(0, int(y))
        self.x2 = min(self.w - 1, int(x + bw))
        self.y2 = min(self.h - 1, int(y + bh))

        self.target_region = self.image[self.y1:self.y2, self.x1:self.x2]

    def extract(self) -> FingerprintResult:
        result = FingerprintResult()

        if self.target_region.size == 0:
            logger.warning("Empty target region — returning unavailable fingerprint.")
            return result

        result.backscatter_score, result.raw_features['backscatter'] = self._backscatter()
        result.texture_score, result.raw_features['texture'] = self._texture()
        result.geometry_score, result.raw_features['geometry'] = self._geometry()
        result.shadow_score, result.raw_features['shadow'] = self._shadow()
        result.object_shadow_score, result.raw_features['object_shadow'] = self._object_shadow_relationship(
            result.raw_features['shadow']
        )
        result.seabed_context_score, result.raw_features['seabed'] = self._seabed_context()
        result.signal_quality_score = min(100.0, max(0.0, self.quality_score))

        # Update statuses
        result.backscatter_status = _score_to_status(result.backscatter_score)
        result.texture_status = _score_to_status(result.texture_score)
        result.geometry_status = _score_to_status(result.geometry_score)
        result.shadow_status = _score_to_status(result.shadow_score)
        result.object_shadow_status = _score_to_status(result.object_shadow_score)
        result.seabed_context_status = _score_to_status(result.seabed_context_score)
        result.signal_quality_status = _score_to_status(result.signal_quality_score)

        return result

    # ----------------------------------------------------------------
    # Cue 1 – Backscatter
    # ----------------------------------------------------------------

    def _backscatter(self):
        region = self.target_region.astype(float)

        # Intensity relative to global image median
        global_median = float(np.median(self.image[self.image > 5]))
        local_mean = float(np.mean(region))
        local_contrast = float(np.std(region))

        if global_median < 1:
            return 0.0, {}

        relative_intensity = local_mean / global_median

        # Score: higher if target is distinctly brighter than background
        score = 0.0
        if relative_intensity > 1.5:
            score = min(100.0, 60 + (relative_intensity - 1.5) * 40)
        elif relative_intensity > 1.1:
            score = 40 + (relative_intensity - 1.1) * 50
        else:
            score = max(0.0, relative_intensity * 30)

        # Boost for high local contrast
        score = min(100.0, score + min(20.0, local_contrast / 5.0))

        return round(score, 1), {
            'local_mean': round(local_mean, 2),
            'global_median': round(global_median, 2),
            'relative_intensity': round(relative_intensity, 3),
            'local_contrast': round(local_contrast, 2),
        }

    # ----------------------------------------------------------------
    # Cue 2 – Texture
    # ----------------------------------------------------------------

    def _texture(self):
        region = self.target_region.astype(float)
        if region.size < 4:
            return 0.0, {}

        # Variance
        variance = float(np.var(region))

        # Local entropy proxy using histogram
        hist, _ = np.histogram(region.flatten(), bins=32, range=(0, 255))
        hist = hist / (hist.sum() + 1e-8)
        entropy = float(-np.sum(hist * np.log2(hist + 1e-8)))

        # Normalize entropy (max ~5 bits for 32 bins)
        norm_entropy = entropy / 5.0

        # Get background patch for comparison
        bg = self._background_patch()
        bg_var = float(np.var(bg)) if bg.size > 0 else variance

        # Score: if target texture differs significantly from background
        var_ratio = variance / (bg_var + 0.1)
        score = min(100.0, 30 + norm_entropy * 40 + min(30.0, var_ratio * 10))

        return round(score, 1), {
            'variance': round(variance, 2),
            'entropy': round(entropy, 3),
            'bg_variance': round(bg_var, 2),
            'var_ratio': round(var_ratio, 3),
        }

    # ----------------------------------------------------------------
    # Cue 3 – Geometry
    # ----------------------------------------------------------------

    def _geometry(self):
        bw = self.x2 - self.x1
        bh = self.y2 - self.y1
        area = bw * bh

        if area == 0:
            return 0.0, {}

        aspect_ratio = bw / max(bh, 1)

        # Contour analysis on the target region
        region = self.target_region.copy()
        _, binary = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        compactness = 0.0
        regularity = 0.0
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            perimeter = cv2.arcLength(cnt, True)
            cnt_area = cv2.contourArea(cnt)
            if perimeter > 0:
                compactness = 4 * np.pi * cnt_area / (perimeter ** 2)
            if cnt_area > 0:
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                regularity = cnt_area / max(hull_area, 1)

        # Score: reward distinct geometry (reasonable aspect ratio, compactness)
        score = 50.0
        # Size score: penalise very small or very large
        min_area, max_area = 25, 50000
        if min_area <= area <= max_area:
            score += 15.0
        else:
            score -= 10.0

        # Aspect ratio: marine debris often 1–5 range
        if 0.2 <= aspect_ratio <= 8:
            score += 15.0

        score += compactness * 20.0  # 0–20
        score = min(100.0, max(0.0, score))

        return round(score, 1), {
            'width': bw,
            'height': bh,
            'area': area,
            'aspect_ratio': round(aspect_ratio, 3),
            'compactness': round(compactness, 3),
            'regularity': round(regularity, 3),
        }

    # ----------------------------------------------------------------
    # Cue 4 – Acoustic Shadow
    # ----------------------------------------------------------------

    def _shadow(self):
        """
        Analyze the dark region behind the target (shadow tail).
        For a side-scan sonar image, shadow falls on the far-range side of the target.
        """
        bw = self.x2 - self.x1
        bh = self.y2 - self.y1

        # Shadow is expected in the across-track direction past the target
        shadow_x1 = self.x2
        shadow_x2 = min(self.w - 1, self.x2 + bw * 2)
        shadow_y1 = max(0, self.y1)
        shadow_y2 = min(self.h - 1, self.y2)

        if shadow_x2 <= shadow_x1 or shadow_y2 <= shadow_y1:
            return 20.0, {'status': 'region_out_of_bounds'}

        shadow_region = self.image[shadow_y1:shadow_y2, shadow_x1:shadow_x2].astype(float)
        if shadow_region.size == 0:
            return 20.0, {}

        target_mean = float(np.mean(self.target_region))
        shadow_mean = float(np.mean(shadow_region))
        global_mean = float(np.mean(self.image))

        # Shadow should be darker than both target and background
        shadow_present = shadow_mean < (global_mean * 0.7)
        shadow_strength = max(0.0, (global_mean - shadow_mean) / max(global_mean, 1)) * 100

        extent = (shadow_x2 - shadow_x1) / max(bw, 1)
        extent_score = min(30.0, extent * 10)

        score = 0.0
        if shadow_present:
            score = min(100.0, shadow_strength * 0.7 + extent_score)
        else:
            score = max(0.0, shadow_strength * 0.3)

        return round(score, 1), {
            'shadow_mean': round(shadow_mean, 2),
            'target_mean': round(target_mean, 2),
            'global_mean': round(global_mean, 2),
            'shadow_present': shadow_present,
            'shadow_strength': round(shadow_strength, 2),
            'extent_ratio': round(extent, 3),
        }

    # ----------------------------------------------------------------
    # Cue 5 – Object-Shadow Relationship
    # ----------------------------------------------------------------

    def _object_shadow_relationship(self, shadow_features: dict):
        """
        Check whether the object and its shadow are geometrically consistent.
        A real object should have shadow length proportional to its height.
        """
        bw = self.x2 - self.x1
        bh = self.y2 - self.y1

        shadow_present = shadow_features.get('shadow_present', False)
        extent_ratio = shadow_features.get('extent_ratio', 0.0)
        shadow_strength = shadow_features.get('shadow_strength', 0.0)

        if not shadow_present:
            # Some objects may not cast strong shadows depending on altitude
            return 35.0, {'consistency': 'no_shadow'}

        # Check proportionality: shadow should extend but not impossibly far
        if 0.3 <= extent_ratio <= 10.0:
            proportional = True
            consistency_score = 70.0
        else:
            proportional = False
            consistency_score = 30.0

        # Reward: strong shadow with reasonable extent
        score = consistency_score + min(30.0, shadow_strength * 0.2)
        score = min(100.0, max(0.0, score))

        return round(score, 1), {
            'proportional': proportional,
            'extent_ratio': round(extent_ratio, 3),
            'shadow_strength': round(shadow_strength, 2),
        }

    # ----------------------------------------------------------------
    # Cue 6 – Seabed Context
    # ----------------------------------------------------------------

    def _seabed_context(self):
        """
        Compare target region against nearby seabed.
        High difference = target is anomalous relative to seabed.
        """
        bg = self._background_patch()
        if bg.size == 0:
            return 40.0, {'status': 'no_background_available'}

        target_mean = float(np.mean(self.target_region))
        bg_mean = float(np.mean(bg))
        target_std = float(np.std(self.target_region))
        bg_std = float(np.std(bg))

        intensity_diff = abs(target_mean - bg_mean)
        texture_diff = abs(target_std - bg_std)

        # Score: how different is the target from background
        intensity_score = min(60.0, intensity_diff / max(bg_mean, 1) * 100)
        texture_score = min(40.0, texture_diff / max(bg_std, 1) * 40)
        score = intensity_score + texture_score
        score = min(100.0, max(0.0, score))

        return round(score, 1), {
            'target_mean': round(target_mean, 2),
            'bg_mean': round(bg_mean, 2),
            'intensity_diff': round(intensity_diff, 2),
            'texture_diff': round(texture_diff, 2),
        }

    # ----------------------------------------------------------------
    # Utility
    # ----------------------------------------------------------------

    def _background_patch(self) -> np.ndarray:
        """Extract a background patch near the target (avoiding nadir)."""
        bw = self.x2 - self.x1
        bh = self.y2 - self.y1
        pad = max(bw, bh)

        # Try to get a patch above the target
        bg_y1 = max(0, self.y1 - pad)
        bg_y2 = max(0, self.y1 - 5)
        bg_x1 = self.x1
        bg_x2 = self.x2

        if bg_y2 > bg_y1 and bg_x2 > bg_x1:
            patch = self.image[bg_y1:bg_y2, bg_x1:bg_x2]
            if patch.size > 10:
                return patch.astype(float)

        # Fallback: patch to the left
        bg_x1 = max(0, self.x1 - pad * 2)
        bg_x2 = max(0, self.x1 - 5)

        # Avoid nadir
        if self.nadir_start is not None:
            bg_x1 = max(bg_x1, self.nadir_end or 0)

        if bg_x2 > bg_x1:
            patch = self.image[self.y1:self.y2, bg_x1:bg_x2]
            return patch.astype(float)

        return np.array([])
