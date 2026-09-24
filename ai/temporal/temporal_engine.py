"""
SONAR-X Temporal Intelligence Engine

Matches detections across repeat surveys using:
- Haversine spatial filtering
- Classification compatibility
- Fingerprint similarity scoring

IMPORTANT SCIENTIFIC CONSTRAINTS:
- "POTENTIALLY RELOCATED" requires a plausible nearby candidate with
  sufficient fingerprint similarity. It is NOT confirmed movement.
- "NOT DETECTED" does NOT mean the object was removed or moved.
  Absence of detection does not prove absence of object.
- All scores are labelled "Fingerprint Similarity Score" — NOT probability.
- No scientific validation is claimed.
"""

import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger('sonarx.temporal')

# Classification compatibility matrix
# A relocated object should have the same or similar classification
COMPATIBLE_CLASSES = {
    'MARINE_DEBRIS': {'MARINE_DEBRIS', 'UNKNOWN_ANOMALY'},
    'NATURAL_FORMATION': {'NATURAL_FORMATION'},
    'SONAR_ARTIFACT': {'SONAR_ARTIFACT'},
    'UNKNOWN_ANOMALY': {'MARINE_DEBRIS', 'UNKNOWN_ANOMALY', 'NATURAL_FORMATION'},
}


def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Haversine distance in metres."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def fingerprint_similarity(fp1: Dict[str, float], fp2: Dict[str, float]) -> float:
    """
    Compute Fingerprint Similarity Score between two fingerprints.
    Uses cosine similarity on the seven-cue vectors.

    Returns float in [0, 1].
    Labelled as 'Fingerprint Similarity Score' — NOT a probability.
    """
    cues = ['backscatter', 'texture', 'geometry', 'shadow',
            'object_shadow', 'seabed_context', 'signal_quality']

    v1 = [fp1.get(c, 0.0) for c in cues]
    v2 = [fp2.get(c, 0.0) for c in cues]

    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))

    if mag1 < 1e-8 or mag2 < 1e-8:
        return 0.0

    return round(max(0.0, min(1.0, dot / (mag1 * mag2))), 4)


class TemporalMatcher:
    """
    Match a previous observation against candidates in a follow-up survey.

    Parameters
    ----------
    search_radius_m : float
        Maximum search radius in metres for candidate matching.
    similarity_threshold : float
        Minimum fingerprint similarity for POTENTIALLY_RELOCATED.
    """

    def __init__(
        self,
        search_radius_m: float = 500.0,
        similarity_threshold: float = 0.65,
    ):
        self.search_radius_m = search_radius_m
        self.similarity_threshold = similarity_threshold

    def match(
        self,
        previous: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Match a previous detection against follow-up survey candidates.

        Parameters
        ----------
        previous : dict
            Keys: lat, lon, classification, fingerprint (dict)
        candidates : list of dicts
            Each with: lat, lon, classification, fingerprint (dict)

        Returns
        -------
        dict with keys: status, matched_candidate, distance_m, similarity, notes
        """
        prev_lat = previous.get('latitude')
        prev_lon = previous.get('longitude')

        if prev_lat is None or prev_lon is None:
            return {
                'status': 'REQUIRES_VERIFICATION',
                'matched_candidate': None,
                'distance_m': None,
                'similarity': None,
                'notes': 'Previous detection had no GPS coordinates. Spatial matching unavailable.',
            }

        # Filter candidates within search radius
        nearby = []
        for c in candidates:
            c_lat = c.get('latitude')
            c_lon = c.get('longitude')
            if c_lat is None or c_lon is None:
                continue
            dist = haversine_distance(prev_lat, prev_lon, c_lat, c_lon)
            if dist <= self.search_radius_m:
                nearby.append({**c, '_distance_m': dist})

        # Case B: no candidates nearby → NOT DETECTED
        if not nearby:
            return {
                'status': 'NOT_DETECTED',
                'matched_candidate': None,
                'distance_m': None,
                'similarity': None,
                'notes': (
                    'No candidate detected within search radius at previous location. '
                    'This does NOT confirm the object was removed or moved — '
                    'it may be undetected due to survey geometry, conditions, or nadir overlap.'
                ),
            }

        prev_class = previous.get('classification', 'UNKNOWN_ANOMALY')
        prev_fp = previous.get('fingerprint', {})

        # Score nearby candidates
        scored = []
        for c in nearby:
            # Check classification compatibility
            compatible_classes = COMPATIBLE_CLASSES.get(prev_class, set())
            class_compatible = c.get('classification', '') in compatible_classes

            # Fingerprint similarity
            sim = fingerprint_similarity(prev_fp, c.get('fingerprint', {}))
            dist = c['_distance_m']

            # Combined score (distance-weighted)
            distance_factor = max(0.0, 1.0 - dist / self.search_radius_m)
            combined = sim * 0.7 + distance_factor * 0.3
            if not class_compatible:
                combined *= 0.5

            scored.append({
                'candidate': c,
                'distance_m': dist,
                'similarity': sim,
                'combined': combined,
                'class_compatible': class_compatible,
            })

        scored.sort(key=lambda x: x['combined'], reverse=True)
        best = scored[0]

        # Case A: candidate close to original location → STILL PRESENT
        if best['distance_m'] < 50 and best['similarity'] >= self.similarity_threshold:
            return {
                'status': 'STILL_PRESENT',
                'matched_candidate': best['candidate'],
                'distance_m': round(best['distance_m'], 1),
                'similarity': best['similarity'],
                'notes': (
                    f'Candidate detected within {best["distance_m"]:.0f}m of original location '
                    f'with Fingerprint Similarity Score {best["similarity"]:.2f}.'
                ),
            }

        # Case C: different location, strong similarity → POTENTIALLY RELOCATED
        if best['similarity'] >= self.similarity_threshold:
            return {
                'status': 'POTENTIALLY_RELOCATED',
                'matched_candidate': best['candidate'],
                'distance_m': round(best['distance_m'], 1),
                'similarity': best['similarity'],
                'notes': (
                    f'Object not detected at original location. '
                    f'Nearby candidate at {best["distance_m"]:.0f}m has '
                    f'Fingerprint Similarity Score of {best["similarity"]:.2f}. '
                    'POTENTIALLY RELOCATED — requires human verification. '
                    'This is NOT confirmed movement.'
                ),
            }

        # Case D: partial similarity → POSSIBLE MATCH
        if best['similarity'] >= 0.40:
            return {
                'status': 'POSSIBLE_MATCH',
                'matched_candidate': best['candidate'],
                'distance_m': round(best['distance_m'], 1),
                'similarity': best['similarity'],
                'notes': (
                    f'Possible match at {best["distance_m"]:.0f}m with '
                    f'Fingerprint Similarity Score {best["similarity"]:.2f}. '
                    'Evidence insufficient for confident association. Requires verification.'
                ),
            }

        # Not a confident match
        return {
            'status': 'REQUIRES_VERIFICATION',
            'matched_candidate': best['candidate'],
            'distance_m': round(best['distance_m'], 1),
            'similarity': best['similarity'],
            'notes': (
                f'Nearby candidate found but fingerprint similarity ({best["similarity"]:.2f}) '
                'is below threshold. Manual review required.'
            ),
        }
