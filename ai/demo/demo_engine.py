"""
SONAR-X Demo Engine
Provides deterministic cached demo results for SIH judging.

ALL demo results are clearly labelled:
- DATA SOURCE: DEMO
- Inference Mode: DEMO
- data is synthetic — not field performance
"""

from typing import List, Dict, Any

DEMO_VERSION = '0.1.0-prototype'

# Deterministic demo detections for the Arabian Sea Demo Survey
DEMO_DETECTIONS: List[Dict[str, Any]] = [
    {
        'debris_uid': 'SX-DB-0001',
        'demo_image_key': 'marine_debris_01',
        'classification': 'MARINE_DEBRIS',
        'confidence': 78,
        'evidence_score': 81,
        'false_positive_risk': 'LOW',
        'fingerprint': {
            'backscatter': 82,
            'texture': 71,
            'geometry': 88,
            'shadow': 76,
            'object_shadow': 81,
            'seabed_context': 69,
            'signal_quality': 91,
        },
        'hazard': {
            'level': 'NONE',
            'score': 15,
            'indicators': [],
            'limited_data': False,
        },
        'explanation': {
            'supporting': [
                'Distinct object geometry with regular contour',
                'Localized high acoustic backscatter',
                'Consistent acoustic shadow present',
                'Target texture differs from surrounding seabed',
            ],
            'counter_evidence': [
                'Signal quality moderate in this region',
            ],
        },
        'location': {'latitude': 19.4521, 'longitude': 72.8403},
        'processing': {
            'nadir': 'APPLIED',
            'gain': 'APPLIED',
            'slant_range': 'ESTIMATED',
            'quality': 'GOOD',
        },
        'bbox': [120, 80, 45, 30],
        'data_source': 'DEMO',
        'inference_mode': 'DEMO',
        'temporal_status': 'POTENTIALLY_RELOCATED',
        'verification_status': 'PENDING',
    },
    {
        'debris_uid': 'SX-DB-0002',
        'demo_image_key': 'natural_formation_01',
        'classification': 'NATURAL_FORMATION',
        'confidence': 72,
        'evidence_score': 68,
        'false_positive_risk': 'LOW',
        'fingerprint': {
            'backscatter': 55,
            'texture': 78,
            'geometry': 45,
            'shadow': 35,
            'object_shadow': 40,
            'seabed_context': 30,
            'signal_quality': 88,
        },
        'hazard': {
            'level': 'NONE',
            'score': 0,
            'indicators': [],
            'limited_data': False,
        },
        'explanation': {
            'supporting': [
                'Diffuse texture consistent with natural sediment ripples',
                'Irregular outline without defined edges',
                'Low contrast relative to background seabed',
            ],
            'counter_evidence': [
                'Backscatter slightly elevated at edges',
            ],
        },
        'location': {'latitude': 19.4498, 'longitude': 72.8435},
        'processing': {
            'nadir': 'APPLIED',
            'gain': 'APPLIED',
            'slant_range': 'ESTIMATED',
            'quality': 'GOOD',
        },
        'bbox': [280, 120, 80, 55],
        'data_source': 'DEMO',
        'inference_mode': 'DEMO',
        'temporal_status': None,
        'verification_status': 'PENDING',
    },
    {
        'debris_uid': 'SX-DB-0003',
        'demo_image_key': 'sonar_artifact_01',
        'classification': 'SONAR_ARTIFACT',
        'confidence': 85,
        'evidence_score': 82,
        'false_positive_risk': 'LOW',
        'fingerprint': {
            'backscatter': 45,
            'texture': 30,
            'geometry': 25,
            'shadow': 15,
            'object_shadow': 20,
            'seabed_context': 35,
            'signal_quality': 72,
        },
        'hazard': {
            'level': 'NONE',
            'score': 0,
            'indicators': [],
            'limited_data': False,
        },
        'explanation': {
            'supporting': [
                'Linear feature aligned with sonar track',
                'Uniform intensity across entire stripe',
                'No corresponding acoustic shadow',
                'Consistent with dropout line artifact',
            ],
            'counter_evidence': [],
        },
        'location': {'latitude': None, 'longitude': None},
        'processing': {
            'nadir': 'APPLIED',
            'gain': 'APPLIED',
            'slant_range': 'NOT_APPLIED',
            'quality': 'MODERATE',
        },
        'bbox': [0, 195, 512, 8],
        'data_source': 'DEMO',
        'inference_mode': 'DEMO',
        'temporal_status': None,
        'verification_status': 'PENDING',
    },
    {
        'debris_uid': 'SX-DB-0004',
        'demo_image_key': 'unknown_anomaly_01',
        'classification': 'UNKNOWN_ANOMALY',
        'confidence': 41,
        'evidence_score': 45,
        'false_positive_risk': 'MEDIUM',
        'fingerprint': {
            'backscatter': 62,
            'texture': 48,
            'geometry': 55,
            'shadow': 38,
            'object_shadow': 42,
            'seabed_context': 58,
            'signal_quality': 65,
        },
        'hazard': {
            'level': 'CAUTION',
            'score': 35,
            'indicators': ['Unknown class with ambiguous acoustic evidence'],
            'limited_data': False,
        },
        'explanation': {
            'supporting': [
                'Elevated backscatter relative to surrounding seabed',
                'Partial acoustic shadow detected',
            ],
            'counter_evidence': [
                'Geometry ambiguous — does not match typical debris profile',
                'Shadow consistency weak',
                'Evidence insufficient for definitive classification',
            ],
        },
        'location': {'latitude': 19.4510, 'longitude': 72.8418},
        'processing': {
            'nadir': 'APPLIED',
            'gain': 'APPLIED',
            'slant_range': 'ESTIMATED',
            'quality': 'MODERATE',
        },
        'bbox': [195, 140, 35, 28],
        'data_source': 'DEMO',
        'inference_mode': 'DEMO',
        'temporal_status': None,
        'verification_status': 'PENDING',
    },
    {
        'debris_uid': 'SX-DB-0005',
        'demo_image_key': 'potential_hazard_01',
        'classification': 'UNKNOWN_ANOMALY',
        'confidence': 64,
        'evidence_score': 72,
        'false_positive_risk': 'MEDIUM',
        'fingerprint': {
            'backscatter': 88,
            'texture': 75,
            'geometry': 84,
            'shadow': 82,
            'object_shadow': 79,
            'seabed_context': 77,
            'signal_quality': 85,
        },
        'hazard': {
            'level': 'HIGH_CAUTION',
            'score': 78,
            'indicators': [
                'Large spatial extent',
                'Regular / structured geometry',
                'Strong acoustic backscatter',
                'Prominent acoustic shadow',
                'Unknown class with strong acoustic evidence',
            ],
            'limited_data': False,
            'banner_text': 'POTENTIAL HAZARD — DO NOT DISTURB',
        },
        'explanation': {
            'supporting': [
                'Large distinct target with strong backscatter return',
                'Regular geometric profile with defined edges',
                'Prominent and proportional acoustic shadow',
                'Target clearly anomalous relative to surrounding seabed',
            ],
            'counter_evidence': [
                'Classification is uncertain — insufficient discriminating features for definitive class',
            ],
        },
        'location': {'latitude': 19.4530, 'longitude': 72.8445},
        'processing': {
            'nadir': 'APPLIED',
            'gain': 'APPLIED',
            'slant_range': 'APPLIED',
            'quality': 'GOOD',
        },
        'bbox': [150, 90, 90, 60],
        'data_source': 'DEMO',
        'inference_mode': 'DEMO',
        'temporal_status': 'POTENTIALLY_RELOCATED',
        'verification_status': 'PENDING',
    },
]

# Temporal demo scenario
DEMO_TEMPORAL_SCENARIO = {
    'debris_uid': 'SX-DB-0001',
    'survey_1': {
        'survey_name': 'Arabian Sea — Demo Survey',
        'date': '2024-03-15',
        'location': {'latitude': 19.4521, 'longitude': 72.8403},
        'classification': 'MARINE_DEBRIS',
        'status': 'DETECTED',
    },
    'survey_2': {
        'survey_name': 'Arabian Sea — Follow-up Survey',
        'date': '2024-06-20',
        'original_location': {'latitude': 19.4521, 'longitude': 72.8403},
        'candidate_location': {'latitude': 19.4535, 'longitude': 72.8421},
        'distance_m': 182.4,
        'fingerprint_similarity': 0.74,
        'status': 'POTENTIALLY_RELOCATED',
        'note': (
            'POTENTIALLY RELOCATED — object not detected at original location. '
            'Nearby candidate (≈182 m) has Fingerprint Similarity Score of 0.74. '
            'Human verification required before confirming relocation.'
        ),
    },
}


def get_demo_detections() -> List[Dict[str, Any]]:
    """Return deterministic demo detections. Always labelled DEMO."""
    return DEMO_DETECTIONS


def get_demo_temporal_scenario() -> Dict[str, Any]:
    """Return the deterministic demo temporal scenario."""
    return DEMO_TEMPORAL_SCENARIO


def get_demo_survey_info() -> Dict[str, Any]:
    return {
        'name': 'Arabian Sea — Demo Survey',
        'date': '2024-03-15',
        'area': 'Arabian Sea — Western Coast',
        'operator': 'Team Kurukshetra',
        'data_source': 'DEMO',
        'is_demo': True,
        'latitude': 19.4521,
        'longitude': 72.8403,
        'altitude_m': 2.5,
        'range_scale_mpp': 0.2,
        'channel_layout': 'BOTH',
        'notes': (
            'Arabian Sea demonstration survey. '
            'DATA SOURCE: DEMO — Synthetic data — not field performance. '
            'All results are deterministic demo outputs.'
        ),
    }
