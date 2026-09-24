"""
SONAR-X Demo Data Seeder
Creates demo users, demo survey, and deterministic demo detections.
"""

import sys
import os
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Seed SONAR-X with demo data for SIH demonstration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('[*] Seeding SONAR-X demo data...'))

        # 1. Create demo user
        from accounts.models import User
        demo_user, created = User.objects.get_or_create(
            email='demo@sonarx.ai',
            defaults={
                'first_name': 'Demo',
                'last_name': 'User',
                'role': 'DEMO',
                'organisation': 'Team Kurukshetra',
                'is_active': True,
            }
        )
        if created:
            demo_user.set_password('demo123')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS('  [OK] Demo user created: demo@sonarx.ai / demo123'))
        else:
            demo_user.set_password('demo123')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS('  [OK] Demo user updated'))

        # 2. Create demo survey
        from surveys.models import Survey
        survey, created = Survey.objects.get_or_create(
            survey_id='SX-SRV-DEMO-001',
            defaults={
                'name': 'Arabian Sea — Demo Survey',
                'date': datetime.date(2024, 3, 15),
                'area': 'Arabian Sea — Western Coast',
                'operator': 'Team Kurukshetra',
                'created_by': demo_user,
                'data_source': 'DEMO',
                'status': 'COMPLETED',
                'altitude_m': 2.5,
                'range_scale_mpp': 0.2,
                'channel_layout': 'BOTH',
                'latitude': 19.4521,
                'longitude': 72.8403,
                'is_demo': True,
                'notes': (
                    'Arabian Sea demonstration survey. '
                    'DATA SOURCE: DEMO — Synthetic data — not field performance. '
                    'All results are deterministic demo outputs for SIH presentation.'
                ),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  [OK] Demo survey created: {survey.survey_id}'))

        # 3. Create follow-up survey
        followup, created = Survey.objects.get_or_create(
            survey_id='SX-SRV-DEMO-002',
            defaults={
                'name': 'Arabian Sea — Follow-up Survey',
                'date': datetime.date(2024, 6, 20),
                'area': 'Arabian Sea — Western Coast',
                'operator': 'Team Kurukshetra',
                'created_by': demo_user,
                'data_source': 'DEMO',
                'status': 'COMPLETED',
                'altitude_m': 2.5,
                'range_scale_mpp': 0.2,
                'channel_layout': 'BOTH',
                'latitude': 19.4521,
                'longitude': 72.8403,
                'is_demo': True,
                'notes': 'Follow-up survey for temporal intelligence demonstration.',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  [OK] Follow-up survey created: {followup.survey_id}'))

        # 4. Create demo sonar files
        from sonar.models import SonarFile
        demo_keys = [
            'marine_debris_01', 'natural_formation_01',
            'sonar_artifact_01', 'unknown_anomaly_01', 'potential_hazard_01',
        ]
        sonar_files = {}
        for key in demo_keys:
            sf, created = SonarFile.objects.get_or_create(
                survey=survey,
                demo_image_key=key,
                defaults={
                    'filename': f'{key}.png',
                    'file_type': 'DEMO',
                    'width': 512,
                    'height': 256,
                    'is_grayscale': True,
                    'is_demo': True,
                    'data_source': 'DEMO',
                    'status': 'PREPROCESSED',
                    'quality_score': 82.0,
                    'quality_level': 'GOOD',
                    'saturation_ratio': 0.02,
                    'dropout_ratio': 0.01,
                    'snr_proxy': 12.5,
                    'nadir_width_px': 40,
                    'image_contrast': 65.0,
                    'usable_area_ratio': 0.91,
                }
            )
            sonar_files[key] = sf

        # 5. Create demo detections
        from detections.models import Detection, SonarFingerprint, DebrisObject, DetectionObservation

        sys.path.insert(0, str(settings.AI_DIR))
        try:
            from demo.demo_engine import get_demo_detections
            demo_dets = get_demo_detections()
        except ImportError:
            demo_dets = []

        for det_data in demo_dets:
            debris_uid = det_data.get('debris_uid', '')
            existing = Detection.objects.filter(
                survey=survey,
                debris_uid=debris_uid,
            ).first()

            if not existing:
                image_key = det_data.get('demo_image_key', 'marine_debris_01')
                sonar_file = sonar_files.get(image_key, list(sonar_files.values())[0])

                bbox = det_data.get('bbox', [100, 80, 40, 30])
                loc = det_data.get('location', {})

                det = Detection.objects.create(
                    detection_uid=f"SX-DET-{survey.survey_id}-{det_data['debris_uid'][-4:]}",
                    survey=survey,
                    sonar_file=sonar_file,
                    classification=det_data['classification'],
                    confidence=det_data['confidence'],
                    evidence_score=det_data['evidence_score'],
                    false_positive_risk=det_data['false_positive_risk'],
                    bbox_x=bbox[0], bbox_y=bbox[1], bbox_w=bbox[2], bbox_h=bbox[3],
                    latitude=loc.get('latitude'),
                    longitude=loc.get('longitude'),
                    coordinate_source='DEMO' if loc.get('latitude') else '',
                    coordinate_note=(
                        '' if loc.get('latitude') else
                        'Geolocation unavailable for this detection.'
                    ),
                    hazard_level=det_data['hazard'].get('level', 'NONE'),
                    hazard_score=det_data['hazard'].get('score', 0),
                    hazard_indicators=det_data['hazard'].get('indicators', []),
                    hazard_limited_data=det_data['hazard'].get('limited_data', False),
                    recommended_action=(
                        'Do not disturb. Human expert review required.'
                        if det_data['hazard'].get('level') == 'HIGH_CAUTION'
                        else 'Standard survey documentation.'
                    ),
                    supporting_evidence=det_data['explanation'].get('supporting', []),
                    counter_evidence=det_data['explanation'].get('counter_evidence', []),
                    inference_mode='DEMO',
                    data_source='DEMO',
                    processing_summary=det_data.get('processing', {}),
                    debris_uid=debris_uid,
                    temporal_status=det_data.get('temporal_status'),
                    is_demo=True,
                    verification_status='PENDING',
                )

                # Create fingerprint
                fp_data = det_data.get('fingerprint', {})
                fp_data_list = [
                    fp_data.get('backscatter', 0), fp_data.get('texture', 0),
                    fp_data.get('geometry', 0), fp_data.get('shadow', 0),
                    fp_data.get('object_shadow', 0), fp_data.get('seabed_context', 0),
                    fp_data.get('signal_quality', 0),
                ]
                evidence = sum(fp_data_list) / len(fp_data_list) if fp_data_list else 0

                def _status(score):
                    if score >= 70: return 'STRONG'
                    elif score >= 40: return 'MODERATE'
                    elif score > 0: return 'WEAK'
                    return 'UNAVAILABLE'

                SonarFingerprint.objects.create(
                    detection=det,
                    backscatter_score=fp_data.get('backscatter', 0),
                    backscatter_status=_status(fp_data.get('backscatter', 0)),
                    texture_score=fp_data.get('texture', 0),
                    texture_status=_status(fp_data.get('texture', 0)),
                    geometry_score=fp_data.get('geometry', 0),
                    geometry_status=_status(fp_data.get('geometry', 0)),
                    shadow_score=fp_data.get('shadow', 0),
                    shadow_status=_status(fp_data.get('shadow', 0)),
                    object_shadow_score=fp_data.get('object_shadow', 0),
                    object_shadow_status=_status(fp_data.get('object_shadow', 0)),
                    seabed_context_score=fp_data.get('seabed_context', 0),
                    seabed_context_status=_status(fp_data.get('seabed_context', 0)),
                    signal_quality_score=fp_data.get('signal_quality', 0),
                    signal_quality_status=_status(fp_data.get('signal_quality', 0)),
                    evidence_score=det_data.get('evidence_score', evidence),
                )

                # Create debris object and observation
                debris_obj, _ = DebrisObject.objects.get_or_create(
                    debris_uid=debris_uid,
                    defaults={
                        'current_status': 'NEW_DETECTION',
                        'classification': det_data['classification'],
                        'hazard_level': det_data['hazard'].get('level', 'NONE'),
                        'is_demo': True,
                    }
                )
                DetectionObservation.objects.create(
                    debris_object=debris_obj,
                    survey=survey,
                    detection=det,
                    latitude=loc.get('latitude'),
                    longitude=loc.get('longitude'),
                    classification=det_data['classification'],
                    confidence=det_data['confidence'],
                    hazard_level=det_data['hazard'].get('level', 'NONE'),
                    fingerprint_snapshot=det_data.get('fingerprint', {}),
                )

                self.stdout.write(
                    self.style.SUCCESS(f'  [OK] Detection created: {det.detection_uid} ({det.classification})')
                )

        # 6. Create temporal scenario (potentially relocated case)
        self._create_temporal_scenario(survey, followup, demo_user)

        self.stdout.write(self.style.SUCCESS('\n[DONE] Demo data seeded successfully!'))
        self.stdout.write(self.style.NOTICE('   Login: demo@sonarx.ai / demo123'))

    def _create_temporal_scenario(self, survey1, survey2, demo_user):
        """Create the demo temporal relocation scenario."""
        from detections.models import (
            Detection, SonarFingerprint, DebrisObject,
            DetectionObservation, TemporalMatch
        )
        from sonar.models import SonarFile

        debris = DebrisObject.objects.filter(debris_uid='SX-DB-0001').first()
        if not debris:
            return

        # Follow-up: not detected at original location, but candidate nearby
        sonar_file2, _ = SonarFile.objects.get_or_create(
            survey=survey2,
            demo_image_key='marine_debris_relocated',
            defaults={
                'filename': 'marine_debris_relocated.png',
                'file_type': 'DEMO',
                'width': 512, 'height': 256,
                'is_grayscale': True, 'is_demo': True, 'data_source': 'DEMO',
                'status': 'PREPROCESSED', 'quality_score': 79.0, 'quality_level': 'GOOD',
            }
        )

        # Candidate detection in follow-up survey (~180m away)
        candidate_det, created = Detection.objects.get_or_create(
            survey=survey2,
            debris_uid='SX-DB-0001-CANDIDATE',
            defaults={
                'detection_uid': f'SX-DET-{survey2.survey_id}-0001C',
                'sonar_file': sonar_file2,
                'classification': 'MARINE_DEBRIS',
                'confidence': 71,
                'evidence_score': 74,
                'false_positive_risk': 'MEDIUM',
                'bbox_x': 130, 'bbox_y': 85, 'bbox_w': 42, 'bbox_h': 28,
                'latitude': 19.4535,
                'longitude': 72.8421,
                'coordinate_source': 'DEMO',
                'hazard_level': 'NONE',
                'hazard_score': 10,
                'hazard_indicators': [],
                'supporting_evidence': [
                    'Similar acoustic profile to SX-DB-0001',
                    'Distinct object geometry',
                    'Acoustic shadow present',
                ],
                'counter_evidence': [
                    'Detected ~182m from original location',
                    'Confidence lower than initial detection',
                ],
                'inference_mode': 'DEMO',
                'data_source': 'DEMO',
                'processing_summary': {'nadir': 'APPLIED', 'gain': 'APPLIED'},
                'temporal_status': 'POTENTIALLY_RELOCATED',
                'is_demo': True,
                'verification_status': 'PENDING',
            }
        )

        if created:
            SonarFingerprint.objects.create(
                detection=candidate_det,
                backscatter_score=79, backscatter_status='STRONG',
                texture_score=68, texture_status='MODERATE',
                geometry_score=82, geometry_status='STRONG',
                shadow_score=71, shadow_status='STRONG',
                object_shadow_score=74, object_shadow_status='STRONG',
                seabed_context_score=65, seabed_context_status='MODERATE',
                signal_quality_score=85, signal_quality_status='STRONG',
                evidence_score=74,
            )

            # Candidate observation
            candidate_obs = DetectionObservation.objects.create(
                debris_object=debris,
                survey=survey2,
                detection=candidate_det,
                latitude=19.4535,
                longitude=72.8421,
                classification='MARINE_DEBRIS',
                confidence=71,
                hazard_level='NONE',
                fingerprint_snapshot={
                    'backscatter': 79, 'texture': 68, 'geometry': 82,
                    'shadow': 71, 'object_shadow': 74, 'seabed_context': 65,
                    'signal_quality': 85,
                },
            )

            # Previous observation
            prev_obs = DetectionObservation.objects.filter(
                debris_object=debris, survey=survey1
            ).first()

            if prev_obs:
                TemporalMatch.objects.create(
                    debris_object=debris,
                    previous_observation=prev_obs,
                    candidate_observation=candidate_obs,
                    distance_m=182.4,
                    fingerprint_similarity=0.74,
                    status='POTENTIALLY_RELOCATED',
                    notes=(
                        'Object not detected at original location. '
                        'Nearby candidate at 182m has Fingerprint Similarity Score 0.74. '
                        'POTENTIALLY RELOCATED — requires human verification. '
                        'This is NOT confirmed movement.'
                    ),
                    is_demo=True,
                )

            debris.current_status = 'POTENTIALLY_RELOCATED'
            debris.save()

            self.stdout.write(self.style.SUCCESS('  [OK] Temporal scenario created: SX-DB-0001 POTENTIALLY RELOCATED'))

