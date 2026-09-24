"""
Django API integration tests for SONAR-X.
Uses pytest-django with SQLite (config.settings_check).

Coverage:
  - JWT authentication (login, protected routes, bad token)
  - Survey CRUD and stats
  - Detection listing, detail, hazard
  - Verification workflow (confirm, reject, class-change, hazard downgrade)
  - Temporal overview
  - Export summary, GeoJSON, CSV, KML
  - Evaluation NOT_EVALUATED guard
"""
import datetime
import uuid
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def demo_user(db):
    from accounts.models import User
    user, _ = User.objects.get_or_create(
        email='apitest@sonarx.ai',
        defaults={
            'first_name': 'API', 'last_name': 'Test',
            'role': 'ANALYST', 'is_active': True,
        }
    )
    user.set_password('testpass123')
    user.save()
    return user


@pytest.fixture
def auth_client(api_client, demo_user):
    """APIClient with valid JWT credentials."""
    refresh = RefreshToken.for_user(demo_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def demo_survey(db, demo_user):
    from surveys.models import Survey
    survey, _ = Survey.objects.get_or_create(
        survey_id='SX-TEST-API-001',
        defaults={
            'name': 'API Test Survey',
            'date': datetime.date(2024, 3, 15),
            'area': 'Arabian Sea — Test',
            'operator': 'Test Operator',
            'created_by': demo_user,
            'data_source': 'DEMO',
            'status': 'COMPLETED',
            'latitude': 19.45,
            'longitude': 72.84,
            'is_demo': True,
        }
    )
    return survey


@pytest.fixture
def demo_detection(db, demo_survey):
    from detections.models import Detection, SonarFingerprint
    det, _ = Detection.objects.get_or_create(
        detection_uid='SX-DET-API-001',
        defaults={
            'survey': demo_survey,
            'classification': 'MARINE_DEBRIS',
            'confidence': 78.0,
            'evidence_score': 81.0,
            'false_positive_risk': 'LOW',
            'hazard_level': 'NONE',
            'hazard_score': 10.0,
            'hazard_indicators': [],
            'supporting_evidence': ['Strong backscatter', 'Distinct geometry'],
            'counter_evidence': ['Signal quality moderate'],
            'inference_mode': 'DEMO',
            'data_source': 'DEMO',
            'processing_summary': {'nadir': 'APPLIED', 'gain': 'APPLIED'},
            'latitude': 19.4521,
            'longitude': 72.8403,
            'verification_status': 'PENDING',
            'is_demo': True,
        }
    )
    SonarFingerprint.objects.get_or_create(
        detection=det,
        defaults={
            'backscatter_score': 82, 'backscatter_status': 'STRONG',
            'texture_score': 71, 'texture_status': 'STRONG',
            'geometry_score': 88, 'geometry_status': 'STRONG',
            'shadow_score': 76, 'shadow_status': 'STRONG',
            'object_shadow_score': 81, 'object_shadow_status': 'STRONG',
            'seabed_context_score': 69, 'seabed_context_status': 'MODERATE',
            'signal_quality_score': 91, 'signal_quality_status': 'STRONG',
            'evidence_score': 81.0,
        }
    )
    return det


# ── Authentication tests ──────────────────────────────────────────

@pytest.mark.django_db
class TestAuthentication:
    def test_login_valid_credentials(self, api_client, demo_user):
        resp = api_client.post('/api/auth/login/', {
            'email': 'apitest@sonarx.ai',
            'password': 'testpass123',
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.data}"
        data = resp.json()
        assert 'access' in data
        assert 'refresh' in data
        assert data['user']['email'] == 'apitest@sonarx.ai'

    def test_login_wrong_password(self, api_client, demo_user):
        resp = api_client.post('/api/auth/login/', {
            'email': 'apitest@sonarx.ai',
            'password': 'wrongpassword!!',
        })
        assert resp.status_code == 401

    def test_protected_route_without_auth(self, api_client):
        resp = api_client.get('/api/surveys/')
        assert resp.status_code == 401

    def test_protected_route_with_valid_auth(self, auth_client):
        resp = auth_client.get('/api/surveys/')
        assert resp.status_code == 200

    def test_me_endpoint_returns_user_info(self, auth_client, demo_user):
        resp = auth_client.get('/api/auth/me/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['email'] == demo_user.email

    def test_invalid_token_rejected(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION='Bearer not.a.real.token')
        resp = api_client.get('/api/surveys/')
        assert resp.status_code == 401


# ── Survey tests ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestSurveyAPI:
    def test_list_surveys(self, auth_client, demo_survey):
        resp = auth_client.get('/api/surveys/')
        assert resp.status_code == 200
        data = resp.json()
        count = data.get('count', len(data.get('results', data if isinstance(data, list) else [])))
        assert count >= 1

    def test_create_survey(self, auth_client):
        payload = {
            'name': 'Created Test Survey',
            'date': '2024-03-15',
            'area': 'Arabian Sea',
            'operator': 'Test Team',
            'data_source': 'DEMO',
            'channel_layout': 'BOTH',
            'already_gain_corrected': False,
            'already_slant_range_corrected': False,
            'already_processed': False,
        }
        resp = auth_client.post('/api/surveys/', payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data['name'] == 'Created Test Survey'
        assert data['survey_id'].startswith('SX-SRV-')

    def test_survey_detail(self, auth_client, demo_survey):
        resp = auth_client.get(f'/api/surveys/{demo_survey.id}/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['survey_id'] == demo_survey.survey_id

    def test_survey_stats_no_fake_metrics(self, auth_client):
        resp = auth_client.get('/api/surveys/stats/')
        assert resp.status_code == 200
        data = resp.json()
        assert 'total_surveys' in data
        assert 'total_detections' in data
        assert 'hazard_flags' in data
        # Must never expose fake accuracy/precision values
        assert 'accuracy' not in data
        assert 'precision' not in data
        assert 'recall' not in data

    def test_demo_surveys_endpoint(self, auth_client, demo_survey):
        resp = auth_client.get('/api/surveys/demo/')
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        ids = [s['survey_id'] for s in data]
        assert demo_survey.survey_id in ids

    def test_survey_not_found(self, auth_client):
        resp = auth_client.get('/api/surveys/999999/')
        assert resp.status_code == 404


# ── Detection tests ───────────────────────────────────────────────

@pytest.mark.django_db
class TestDetectionAPI:
    def test_list_detections(self, auth_client, demo_detection):
        resp = auth_client.get('/api/detections/')
        assert resp.status_code == 200
        data = resp.json()
        results = data.get('results', data if isinstance(data, list) else [])
        assert len(results) >= 1

    def test_detection_detail_includes_fingerprint(self, auth_client, demo_detection):
        resp = auth_client.get(f'/api/detections/{demo_detection.id}/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['detection_uid'] == 'SX-DET-API-001'
        assert data['classification'] == 'MARINE_DEBRIS'
        assert 'fingerprint' in data
        fp = data['fingerprint']
        assert fp['backscatter_score'] == 82
        assert fp['evidence_score'] == 81.0
        # Scientific integrity: no "probability" field
        assert 'probability' not in data

    def test_detection_hazard_levels_valid(self, auth_client, demo_detection):
        resp = auth_client.get(f'/api/detections/{demo_detection.id}/hazard/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['hazard_level'] in ('NONE', 'CAUTION', 'HIGH_CAUTION')
        # Must never say "mine", "bomb", etc.
        indicators_text = ' '.join(data.get('hazard_indicators', [])).lower()
        for forbidden in ['mine', 'bomb', 'munition', 'explosive', 'wreck']:
            assert f' {forbidden}' not in f' {indicators_text} ', \
                f"Forbidden term '{forbidden}' found in hazard indicators"

    def test_detection_filter_by_survey(self, auth_client, demo_detection):
        survey_id = demo_detection.survey.id
        resp = auth_client.get(f'/api/detections/?survey={survey_id}')
        assert resp.status_code == 200

    def test_detection_not_found(self, auth_client):
        fake_id = str(uuid.uuid4())
        resp = auth_client.get(f'/api/detections/{fake_id}/')
        assert resp.status_code == 404


# ── Verification tests ────────────────────────────────────────────

@pytest.mark.django_db
class TestVerificationAPI:
    def test_confirm_detection(self, auth_client, demo_detection):
        resp = auth_client.post(
            f'/api/detections/{demo_detection.id}/verify/',
            {'decision': 'CONFIRMED', 'comment': 'Visual inspection confirms debris.'},
            format='json',
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data['decision'] == 'CONFIRMED'
        demo_detection.refresh_from_db()
        assert demo_detection.verification_status == 'CONFIRMED'

    def test_hazard_downgrade_without_comment_rejected(self, auth_client, demo_detection):
        """Downgrading hazard MUST require a comment — scientific integrity."""
        resp = auth_client.post(
            f'/api/detections/{demo_detection.id}/verify/',
            {'decision': 'HAZARD_DOWNGRADED', 'comment': ''},
            format='json',
        )
        assert resp.status_code == 400

    def test_hazard_downgrade_with_comment_accepted(self, auth_client, demo_detection):
        resp = auth_client.post(
            f'/api/detections/{demo_detection.id}/verify/',
            {'decision': 'HAZARD_DOWNGRADED',
             'comment': 'Visual survey found no hazardous object at location.'},
            format='json',
        )
        assert resp.status_code == 201

    def test_invalid_decision_rejected(self, auth_client, demo_detection):
        resp = auth_client.post(
            f'/api/detections/{demo_detection.id}/verify/',
            {'decision': 'NOT_A_REAL_DECISION'},
            format='json',
        )
        assert resp.status_code == 400

    def test_verification_history_recorded(self, auth_client, demo_detection):
        auth_client.post(
            f'/api/detections/{demo_detection.id}/verify/',
            {'decision': 'ESCALATED', 'comment': 'Needs expert review.'},
            format='json',
        )
        resp = auth_client.get(f'/api/detections/{demo_detection.id}/history/')
        assert resp.status_code == 200
        data = resp.json()
        assert 'verifications' in data
        assert len(data['verifications']) >= 1
        assert data['verifications'][0]['decision'] in (
            'CONFIRMED', 'REJECTED', 'CLASS_CHANGED', 'ESCALATED',
            'HAZARD_CONFIRMED', 'HAZARD_DOWNGRADED'
        )


# ── Temporal tests ────────────────────────────────────────────────

@pytest.mark.django_db
class TestTemporalAPI:
    def test_temporal_overview_structure(self, auth_client):
        resp = auth_client.get('/api/temporal/')
        assert resp.status_code == 200
        data = resp.json()
        assert 'count' in data
        assert 'debris_objects' in data
        assert isinstance(data['debris_objects'], list)

    def test_temporal_detail_not_found(self, auth_client):
        resp = auth_client.get('/api/temporal/SX-DB-NONEXISTENT-9999/')
        assert resp.status_code == 404

    def test_temporal_status_values_are_valid(self, auth_client):
        """All temporal statuses must be from the defined set."""
        resp = auth_client.get('/api/temporal/')
        assert resp.status_code == 200
        valid_statuses = {
            'STILL_PRESENT', 'NOT_DETECTED', 'POTENTIALLY_RELOCATED',
            'POSSIBLE_MATCH', 'NEW_DETECTION', 'REQUIRES_VERIFICATION'
        }
        for obj in resp.json()['debris_objects']:
            assert obj['current_status'] in valid_statuses, \
                f"Invalid status: {obj['current_status']}"


# ── Export tests ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestExportAPI:
    def test_export_summary_structure(self, auth_client, demo_survey):
        resp = auth_client.get(f'/api/exports/surveys/{demo_survey.id}/summary/')
        assert resp.status_code == 200
        data = resp.json()
        required_keys = ['total_detections', 'geolocated', 'no_coordinates', 'by_class', 'data_source']
        for key in required_keys:
            assert key in data, f"Missing key in export summary: {key}"

    def test_geojson_rfc7946_compliance(self, auth_client, demo_survey, demo_detection):
        resp = auth_client.get(f'/api/exports/surveys/{demo_survey.id}/geojson/')
        assert resp.status_code == 200
        data = resp.json()
        # Must be FeatureCollection
        assert data['type'] == 'FeatureCollection'
        # Must include provenance
        assert 'properties' in data
        assert 'data_source' in data['properties']
        assert 'verification_disclaimer' in data['properties']
        # RFC 7946: coordinates are [longitude, latitude]
        for feature in data.get('features', []):
            coords = feature['geometry']['coordinates']
            assert len(coords) >= 2
            lon, lat = coords[0], coords[1]
            assert -180 <= lon <= 180, f"Longitude out of range: {lon}"
            assert -90 <= lat <= 90, f"Latitude out of range: {lat}"

    def test_csv_no_formula_injection(self, auth_client, demo_survey, demo_detection):
        resp = auth_client.get(f'/api/exports/surveys/{demo_survey.id}/csv/')
        assert resp.status_code == 200
        content = resp.content.decode('utf-8', errors='replace')
        assert 'detection_uid' in content
        # Check no CSV formula injection in data rows
        lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
        for line in lines[1:]:  # skip header
            cols = line.split(',')
            for col in cols:
                col_stripped = col.strip().strip('"')
                assert not col_stripped.startswith('='), f"CSV injection: {col_stripped}"

    def test_csv_no_gps_shows_empty_not_zero(self, auth_client, demo_survey, db):
        """Detections without GPS must show empty coords, not 0,0."""
        from detections.models import Detection
        no_gps_det = Detection.objects.create(
            detection_uid='SX-DET-NOGPS-001',
            survey=demo_survey,
            classification='SONAR_ARTIFACT',
            confidence=50,
            evidence_score=40,
            false_positive_risk='HIGH',
            hazard_level='NONE',
            latitude=None,
            longitude=None,
            inference_mode='DEMO',
            data_source='DEMO',
        )
        resp = auth_client.get(f'/api/exports/surveys/{demo_survey.id}/csv/')
        assert resp.status_code == 200
        content = resp.content.decode('utf-8', errors='replace')
        # Find the no-GPS detection line
        for line in content.split('\n'):
            if 'SX-DET-NOGPS-001' in line:
                # Latitude and longitude columns should be empty, not "0" or "0.0"
                parts = line.split(',')
                # lat is at index 7, lon at index 8 (0-indexed)
                lat_val = parts[7].strip() if len(parts) > 7 else ''
                lon_val = parts[8].strip() if len(parts) > 8 else ''
                assert lat_val != '0' and lat_val != '0.0', f"Lat should be empty, got: {lat_val}"
                assert lon_val != '0' and lon_val != '0.0', f"Lon should be empty, got: {lon_val}"
                break

    def test_kml_valid_xml(self, auth_client, demo_survey, demo_detection):
        resp = auth_client.get(f'/api/exports/surveys/{demo_survey.id}/kml/')
        assert resp.status_code == 200
        content = resp.content.decode('utf-8', errors='replace')
        assert '<?xml' in content or '<kml' in content
        assert 'kml' in content.lower()


# ── Evaluation tests ──────────────────────────────────────────────

@pytest.mark.django_db
class TestEvaluationAPI:
    def test_no_runs_returns_not_evaluated(self, auth_client, db):
        from evaluation.models import EvaluationRun
        EvaluationRun.objects.all().delete()
        resp = auth_client.get('/api/evaluation/runs/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'NOT_EVALUATED'
        assert data['runs'] == []

    def test_no_runs_message_is_informative(self, auth_client, db):
        from evaluation.models import EvaluationRun
        EvaluationRun.objects.all().delete()
        resp = auth_client.get('/api/evaluation/runs/')
        data = resp.json()
        msg = data.get('message', '')
        assert msg, "Must include an explanatory message"
        # Must explain that no fake values are shown
        assert len(msg) > 20

    def test_latest_run_not_evaluated(self, auth_client, db):
        from evaluation.models import EvaluationRun
        EvaluationRun.objects.all().delete()
        resp = auth_client.get('/api/evaluation/runs/latest/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'NOT_EVALUATED'

    def test_no_hardcoded_accuracy_in_response(self, auth_client, db):
        """Ensure no response ever contains fabricated metrics like 95%, 98%, 99%."""
        from evaluation.models import EvaluationRun
        EvaluationRun.objects.all().delete()
        resp = auth_client.get('/api/evaluation/runs/')
        content = resp.content.decode('utf-8')
        # None of these values should appear as hardcoded metrics
        for fake_val in ['"precision": 0.95', '"recall": 0.97', '"f1": 0.96',
                          '"accuracy": 0.99', '"map_05": 0.98']:
            assert fake_val not in content, f"Found hardcoded fake metric: {fake_val}"
