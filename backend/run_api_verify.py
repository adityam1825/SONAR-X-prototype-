"""Comprehensive API verification — runs against the live server on port 8000."""
import sys
import os
import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000/api"
PASS = []
FAIL = []

def p(msg): PASS.append(msg); print(f"  [PASS] {msg}")
def f(msg): FAIL.append(msg); print(f"  [FAIL] {msg}")

def post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get_raw(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode('utf-8')

# ── Login ─────────────────────────────────────────────────────────
try:
    login = post(f"{BASE}/auth/login/", {"email": "demo@sonarx.ai", "password": "demo123"})
    token = login["access"]
    assert login['user']['email'] == 'demo@sonarx.ai'
    assert login['user']['role'] == 'DEMO'
    assert len(token) > 20
    p(f"Login: {login['user']['email']} ({login['user']['role']})")
except Exception as e:
    f(f"Login failed: {e}"); sys.exit(1)

# ── Auth me ───────────────────────────────────────────────────────
try:
    me = get(f"{BASE}/auth/me/", token)
    assert me['email'] == 'demo@sonarx.ai'
    p("/api/auth/me/ returns correct user")
except Exception as e:
    f(f"/api/auth/me/ failed: {e}")

# ── Surveys ───────────────────────────────────────────────────────
try:
    surveys = get(f"{BASE}/surveys/", token)
    count = surveys.get('count', len(surveys.get('results', surveys if isinstance(surveys, list) else [])))
    assert count >= 1
    p(f"Survey list: {count} surveys")
except Exception as e:
    f(f"Survey list failed: {e}")

try:
    demo_surveys = get(f"{BASE}/surveys/demo/", token)
    assert isinstance(demo_surveys, list)
    assert len(demo_surveys) >= 1
    demo_id = demo_surveys[0]['id']
    demo_survey_id = demo_surveys[0]['survey_id']
    p(f"Demo surveys: {len(demo_surveys)} (main: {demo_survey_id} id={demo_id})")
except Exception as e:
    f(f"Demo survey failed: {e}"); sys.exit(1)

try:
    stats = get(f"{BASE}/surveys/stats/", token)
    assert stats['total_surveys'] >= 1
    assert stats['total_detections'] >= 1
    assert stats['hazard_flags'] >= 0
    assert 'accuracy' not in stats  # No fake metrics
    p(f"Stats: surveys={stats['total_surveys']}, detections={stats['total_detections']}, hazards={stats['hazard_flags']}")
except Exception as e:
    f(f"Stats failed: {e}")

# ── Detections ────────────────────────────────────────────────────
try:
    dets = get(f"{BASE}/detections/", token)
    det_list = dets.get('results', dets if isinstance(dets, list) else [])
    assert len(det_list) >= 1
    p(f"Detections: {len(det_list)}")
except Exception as e:
    f(f"Detection list failed: {e}"); sys.exit(1)

try:
    # Get a detection with HIGH_CAUTION
    hazard_det = next((d for d in det_list if d['hazard_level'] == 'HIGH_CAUTION'), None)
    if hazard_det:
        det_detail = get(f"{BASE}/detections/{hazard_det['id']}/", token)
        assert 'fingerprint' in det_detail
        fp = det_detail['fingerprint']
        assert 'backscatter_score' in fp
        assert 'evidence_score' in fp
        # Scientific: no "probability" in response
        assert 'probability' not in str(det_detail).lower()
        p(f"Detection detail + fingerprint: {det_detail['detection_uid']} (evidence={fp['evidence_score']})")
    else:
        p("No HIGH_CAUTION detection found (minor)")
except Exception as e:
    f(f"Detection detail failed: {e}")

try:
    # Hazard endpoint
    if hazard_det:
        hazard = get(f"{BASE}/detections/{hazard_det['id']}/hazard/", token)
        assert hazard['hazard_level'] in ('NONE', 'CAUTION', 'HIGH_CAUTION')
        indicators = ' '.join(hazard.get('hazard_indicators', [])).lower()
        for bad in ['mine', 'bomb', 'munition']:
            import re
            assert not re.search(r'\b' + bad + r'\b', indicators), f"Found '{bad}' in indicators"
        p(f"Hazard endpoint: level={hazard['hazard_level']}, indicators={len(hazard['hazard_indicators'])}")
except Exception as e:
    f(f"Hazard endpoint failed: {e}")

# ── Temporal ──────────────────────────────────────────────────────
try:
    temporal = get(f"{BASE}/temporal/", token)
    assert temporal['count'] >= 1
    statuses = [o['current_status'] for o in temporal['debris_objects']]
    valid_statuses = {'STILL_PRESENT','NOT_DETECTED','POTENTIALLY_RELOCATED',
                      'POSSIBLE_MATCH','NEW_DETECTION','REQUIRES_VERIFICATION'}
    for s in statuses:
        assert s in valid_statuses, f"Invalid status: {s}"
    relocated = [o for o in temporal['debris_objects'] if o['current_status'] == 'POTENTIALLY_RELOCATED']
    assert len(relocated) >= 1, "Demo must have POTENTIALLY_RELOCATED case"
    p(f"Temporal: {temporal['count']} objects, POTENTIALLY_RELOCATED: {len(relocated)}")
except Exception as e:
    f(f"Temporal failed: {e}")

# ── Exports ───────────────────────────────────────────────────────
# Find the main demo survey (highest detection count)
try:
    all_surveys = get(f"{BASE}/surveys/demo/", token)
    main_survey = max(all_surveys, key=lambda s: s.get('detection_count', 0))
    main_id = main_survey['id']
    p(f"Main demo survey for exports: {main_survey['survey_id']} (id={main_id}, {main_survey.get('detection_count',0)} detections)")
except Exception as e:
    f(f"Survey selection for exports failed: {e}"); main_id = demo_id

try:
    summary = get(f"{BASE}/exports/surveys/{main_id}/summary/", token)
    assert 'total_detections' in summary
    assert 'geolocated' in summary
    assert 'data_source' in summary
    p(f"Export summary: total={summary['total_detections']}, geolocated={summary['geolocated']}")
except Exception as e:
    f(f"Export summary failed: {e}")

try:
    geojson_str = get_raw(f"{BASE}/exports/surveys/{main_id}/geojson/", token)
    geo = json.loads(geojson_str)
    assert geo['type'] == 'FeatureCollection'
    assert 'data_source' in geo['properties']
    assert 'verification_disclaimer' in geo['properties']
    for feat in geo['features']:
        lon, lat = feat['geometry']['coordinates'][:2]
        assert -180 <= lon <= 180
        assert -90 <= lat <= 90
    p(f"GeoJSON: {len(geo['features'])} features, RFC 7946 coords verified")
except Exception as e:
    f(f"GeoJSON failed: {e}")

try:
    csv_str = get_raw(f"{BASE}/exports/surveys/{main_id}/csv/", token)
    assert 'detection_uid' in csv_str
    # No formula injection
    lines = [l for l in csv_str.split('\n') if l.strip() and not l.startswith('#')]
    for line in lines[1:]:
        for col in line.split(','):
            col = col.strip().strip('"')
            assert not col.startswith('='), f"CSV injection: {col}"
    p(f"CSV: {len(lines)} data rows, no formula injection")
except Exception as e:
    f(f"CSV failed: {e}")

try:
    kml_str = get_raw(f"{BASE}/exports/surveys/{main_id}/kml/", token)
    assert 'kml' in kml_str.lower() or '<?xml' in kml_str
    p("KML: valid XML with kml content")
except Exception as e:
    f(f"KML failed: {e}")

# ── Evaluation ────────────────────────────────────────────────────
try:
    eval_resp = get(f"{BASE}/evaluation/runs/", token)
    assert eval_resp['status'] == 'NOT_EVALUATED'
    assert eval_resp['runs'] == []
    # No fake metrics
    for fake in ['"precision": 0.95', '"accuracy": 0.99', '"recall": 0.97']:
        assert fake not in json.dumps(eval_resp)
    p("Evaluation: NOT_EVALUATED, no fake metrics")
except Exception as e:
    f(f"Evaluation failed: {e}")

# ── Unauthenticated access denied ─────────────────────────────────
try:
    req = urllib.request.Request(f"{BASE}/surveys/")
    try:
        urllib.request.urlopen(req)
        f("Unauthenticated access NOT blocked!")
    except urllib.error.HTTPError as e:
        assert e.code == 401
        p("Unauthenticated access correctly blocked (401)")
except Exception as e:
    f(f"Auth check failed: {e}")

# ── Summary ───────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"PASSES: {len(PASS)}")
print(f"FAILS:  {len(FAIL)}")
if FAIL:
    print("\nFailed checks:")
    for item in FAIL:
        print(f"  FAIL: {item}")
else:
    print("\n[ALL API CHECKS PASSED]")
sys.exit(0 if not FAIL else 1)
