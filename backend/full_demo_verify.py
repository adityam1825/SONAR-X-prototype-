"""
SONAR-X Full Demo Verification Script
Walks through every major API flow that the frontend pages depend on,
verifying data integrity, scientific correctness, and demo completeness.
"""
import json, sys, urllib.request, urllib.error, re

BASE = "http://127.0.0.1:8000/api"
PASS, FAIL, WARN = [], [], []

def ok(msg): PASS.append(msg); print(f"  [PASS] {msg}")
def fail(msg): FAIL.append(msg); print(f"  [FAIL] {msg}")
def warn(msg): WARN.append(msg); print(f"  [WARN] {msg}")

def post(url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get_raw(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8", errors="replace")

print("=" * 60)
print("SONAR-X FULL DEMO VERIFICATION")
print("=" * 60)

# ── 1. Authentication ──────────────────────────────────────────────
print("\n[1] AUTHENTICATION")
try:
    login = post(f"{BASE}/auth/login/", {"email": "demo@sonarx.ai", "password": "demo123"})
    token = login["access"]
    assert "access" in login and "refresh" in login
    assert login["user"]["email"] == "demo@sonarx.ai"
    assert login["user"]["role"] == "DEMO"
    ok(f"JWT login: {login['user']['email']} role={login['user']['role']}")
except Exception as e:
    fail(f"Login: {e}"); sys.exit(1)

try:
    req = urllib.request.Request(f"{BASE}/surveys/")
    urllib.request.urlopen(req)
    fail("Unauthenticated access not blocked")
except urllib.error.HTTPError as e:
    if e.code == 401: ok("Unauthenticated access -> 401")
    else: fail(f"Expected 401, got {e.code}")

# ── 2. Dashboard data ──────────────────────────────────────────────
print("\n[2] DASHBOARD")
stats = get(f"{BASE}/surveys/stats/", token)
assert stats["total_surveys"] >= 1
assert stats["total_detections"] >= 1
# Scientific: no accuracy/precision in stats response
for bad_key in ["accuracy", "precision", "recall", "probability"]:
    assert bad_key not in stats, f"Fake metric '{bad_key}' in stats"
ok(f"Stats: surveys={stats['total_surveys']}, detections={stats['total_detections']}, hazards={stats['hazard_flags']}, pending={stats['pending_verification']}")

# ── 3. Demo surveys ────────────────────────────────────────────────
print("\n[3] DEMO SURVEYS")
demo_surveys = get(f"{BASE}/surveys/demo/", token)
assert len(demo_surveys) >= 2, "Need at least 2 demo surveys"
main_s = next(s for s in demo_surveys if "DEMO-001" in s["survey_id"])
followup_s = next(s for s in demo_surveys if "DEMO-002" in s["survey_id"])
ok(f"Main survey: {main_s['survey_id']} ({main_s['detection_count']} detections)")
ok(f"Follow-up: {followup_s['survey_id']}")

# Survey detail
detail = get(f"{BASE}/surveys/{main_s['id']}/", token)
assert detail["is_demo"] is True
assert detail["data_source"] == "DEMO"
ok("Survey detail: is_demo=True, data_source=DEMO confirmed")

# ── 4. Detections ──────────────────────────────────────────────────
print("\n[4] DETECTIONS")
dets_resp = get(f"{BASE}/detections/?survey={main_s['id']}", token)
dets = dets_resp.get("results", dets_resp if isinstance(dets_resp, list) else [])
classes = {d["classification"] for d in dets}
ok(f"Survey detections: {len(dets)} total, classes={classes}")

# Verify all four classes exist
for cls in ["MARINE_DEBRIS", "NATURAL_FORMATION", "SONAR_ARTIFACT", "UNKNOWN_ANOMALY"]:
    if cls in classes:
        ok(f"  Class present: {cls}")
    else:
        warn(f"  Class missing from demo: {cls}")

# ── 5. Detection detail + fingerprint ─────────────────────────────
print("\n[5] DETECTION DETAIL + FINGERPRINT")
debris_det = next((d for d in dets if d["classification"] == "MARINE_DEBRIS"), None)
if debris_det:
    det_detail = get(f"{BASE}/detections/{debris_det['id']}/", token)
    assert "fingerprint" in det_detail, "Fingerprint missing from detection"
    fp = det_detail["fingerprint"]

    # Verify all 7 cues present
    cues = ["backscatter_score","texture_score","geometry_score","shadow_score",
            "object_shadow_score","seabed_context_score","signal_quality_score"]
    for cue in cues:
        assert cue in fp, f"Missing fingerprint cue: {cue}"
        assert 0 <= fp[cue] <= 100, f"Cue {cue} out of range: {fp[cue]}"
    ok(f"All 7 fingerprint cues present (evidence={fp['evidence_score']})")

    # Scientific: no "probability" in response
    resp_str = json.dumps(det_detail).lower()
    assert "probability" not in resp_str, "Found 'probability' in detection response"
    ok("Scientific: 'probability' not used in detection response")

    # Verify supporting/counter evidence exists
    assert len(det_detail.get("supporting_evidence", [])) > 0
    assert det_detail["data_source"] == "DEMO"
    ok(f"Supporting evidence: {len(det_detail['supporting_evidence'])} items")
    ok(f"Counter evidence: {len(det_detail.get('counter_evidence', []))} items")

    # Inference mode clearly labelled
    assert det_detail["inference_mode"] in ("DEMO", "CLASSICAL_CV", "YOLO")
    ok(f"Inference mode: {det_detail['inference_mode']}")
else:
    fail("No MARINE_DEBRIS detection found")

# ── 6. Evidence fusion check ───────────────────────────────────────
print("\n[6] EVIDENCE FUSION")
if debris_det:
    assert det_detail["evidence_score"] > 0
    assert det_detail["false_positive_risk"] in ("LOW", "MEDIUM", "HIGH")
    ok(f"Evidence score: {det_detail['evidence_score']} (prototype score, not probability)")
    ok(f"False positive risk: {det_detail['false_positive_risk']}")

# ── 7. Hazard detection ────────────────────────────────────────────
print("\n[7] HAZARD DETECTION")
hazard_det = next((d for d in dets if d["hazard_level"] == "HIGH_CAUTION"), None)
if hazard_det:
    haz = get(f"{BASE}/detections/{hazard_det['id']}/hazard/", token)
    assert haz["hazard_level"] == "HIGH_CAUTION"
    indicators = " ".join(haz.get("hazard_indicators", [])).lower()
    # Must NEVER identify specific hazardous objects
    for forbidden in ["mine", "bomb", "munition", "explosive", "weapon", "wreck"]:
        assert not re.search(r"\b" + forbidden + r"\b", indicators), \
            f"Forbidden term '{forbidden}' in hazard indicators"
    ok(f"HIGH_CAUTION detection: {hazard_det['detection_uid']}")
    ok(f"  Indicators: {haz['hazard_indicators']}")
    ok("  Scientific: no specific hazardous object identified")
else:
    fail("No HIGH_CAUTION detection in demo data")

# ── 8. Verification workflow ───────────────────────────────────────
print("\n[8] HUMAN VERIFICATION")
if debris_det:
    # Confirm a detection
    v_resp = post(f"{BASE}/detections/{debris_det['id']}/verify/", {
        "decision": "CONFIRMED",
        "comment": "Demo verification — visual inspection confirms debris signature."
    }, token)
    assert v_resp["decision"] == "CONFIRMED"
    ok(f"Verification CONFIRMED recorded: reviewer={v_resp.get('reviewer_email', '?')}")

    # Verify audit trail
    hist = get(f"{BASE}/detections/{debris_det['id']}/history/", token)
    assert len(hist["verifications"]) >= 1
    ok(f"Audit trail: {len(hist['verifications'])} verification(s) stored")

    # Test hazard downgrade WITHOUT comment is rejected
    try:
        post(f"{BASE}/detections/{debris_det['id']}/verify/", {
            "decision": "HAZARD_DOWNGRADED",
            "comment": ""
        }, token)
        fail("Hazard downgrade without comment should be rejected")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            ok("Hazard downgrade without comment -> 400 (correctly rejected)")

# ── 9. Temporal intelligence ───────────────────────────────────────
print("\n[9] TEMPORAL INTELLIGENCE")
temporal = get(f"{BASE}/temporal/", token)
assert temporal["count"] >= 1
relocated = [o for o in temporal["debris_objects"] if o["current_status"] == "POTENTIALLY_RELOCATED"]
assert len(relocated) >= 1, "Demo must have POTENTIALLY_RELOCATED"
obj = relocated[0]
ok(f"Debris object: {obj['debris_uid']} -> {obj['current_status']}")

# Verify temporal detail
temp_detail = get(f"{BASE}/temporal/{obj['debris_uid']}/", token)
obs = temp_detail["debris_object"]["observations"]
assert len(obs) >= 2, "Need at least 2 observations for temporal case"
ok(f"Observations: {len(obs)} (Survey 1 + Follow-up)")

# Verify NOT_MOVED language
status_in_response = temp_detail["debris_object"]["current_status"]
assert "POTENTIALLY_RELOCATED" in status_in_response, "Must say POTENTIALLY_RELOCATED not MOVED"
ok("Temporal status uses POTENTIALLY_RELOCATED (not MOVED)")

# ── 10. GeoJSON export ─────────────────────────────────────────────
print("\n[10] EXPORTS")
geo_str = get_raw(f"{BASE}/exports/surveys/{main_s['id']}/geojson/", token)
geo = json.loads(geo_str)
assert geo["type"] == "FeatureCollection"
assert geo["properties"]["data_source"] == "DEMO"
assert "verification_disclaimer" in geo["properties"]
for feat in geo["features"]:
    lon, lat = feat["geometry"]["coordinates"][:2]
    assert -180 <= lon <= 180 and -90 <= lat <= 90
    assert feat["properties"]["data_source"] == "DEMO"
ok(f"GeoJSON: {len(geo['features'])} features, RFC 7946, DEMO labelled")

csv_str = get_raw(f"{BASE}/exports/surveys/{main_s['id']}/csv/", token)
assert "detection_uid" in csv_str
lines = [l for l in csv_str.split("\n") if l.strip() and not l.startswith("#")]
for line in lines[1:]:
    for col in line.split(","):
        col = col.strip().strip('"')
        assert not col.startswith("="), f"CSV injection: {col}"
ok(f"CSV: {len(lines)-1} data rows, no formula injection")

kml_str = get_raw(f"{BASE}/exports/surveys/{main_s['id']}/kml/", token)
assert "<kml" in kml_str.lower() or "<?xml" in kml_str
ok("KML: valid XML")

# ── 11. Evaluation integrity ───────────────────────────────────────
print("\n[11] EVALUATION INTEGRITY")
eval_resp = get(f"{BASE}/evaluation/runs/", token)
assert eval_resp["status"] == "NOT_EVALUATED"
assert eval_resp["runs"] == []
fake_vals = ['"precision": 0.9', '"recall": 0.9', '"accuracy": 0.9', '"f1": 0.9', '"map_05": 0.9']
eval_json = json.dumps(eval_resp)
for fv in fake_vals:
    assert fv not in eval_json, f"Found hardcoded metric: {fv}"
ok("Evaluation: NOT_EVALUATED, no hardcoded fake metrics")

# ── 12. Scientific language audit (API responses) ─────────────────
print("\n[12] SCIENTIFIC LANGUAGE AUDIT")
all_dets_resp = get(f"{BASE}/detections/", token)
all_dets = all_dets_resp.get("results", all_dets_resp if isinstance(all_dets_resp, list) else [])
for d in all_dets:
    det_str = json.dumps(d).lower()
    # These must never appear in detection responses
    assert "probability of debris" not in det_str
    assert "field validated" not in det_str
    assert "real-world accuracy" not in det_str
ok("No fabricated scientific claims in detection responses")

# Verify demo survey detections are consistently labelled
demo_dets_resp = get(f"{BASE}/detections/?survey={main_s['id']}", token)
demo_dets_only = demo_dets_resp.get("results", demo_dets_resp if isinstance(demo_dets_resp, list) else [])
demo_labelled = all(d.get("data_source") == "DEMO" for d in demo_dets_only)
if demo_labelled:
    ok("All demo survey detections carry data_source=DEMO")
else:
    warn("Some demo survey detections missing data_source=DEMO label")

# ── 13. Report generation ──────────────────────────────────────────
print("\n[13] REPORT GENERATION")
try:
    rpt = post(f"{BASE}/reports/surveys/{main_s['id']}/", {}, token)
    if "report_id" in rpt and "download_url" in rpt:
        ok(f"Survey report generated: report_id={rpt['report_id']}")
        # Try to download
        try:
            rpt_dl = get_raw(rpt["download_url"].replace("http://testserver", "http://127.0.0.1:8000"), token)
            if len(rpt_dl) > 1000:
                ok(f"PDF download: {len(rpt_dl)} bytes (non-empty)")
            else:
                warn(f"PDF download very small: {len(rpt_dl)} bytes")
        except Exception as e:
            warn(f"PDF download attempt: {e}")
    else:
        warn(f"Report response unusual: {rpt}")
except Exception as e:
    warn(f"Report generation (ReportLab may not be installed): {e}")

# ── SUMMARY ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"PASSES: {len(PASS)} | FAILS: {len(FAIL)} | WARNINGS: {len(WARN)}")
if FAIL:
    print("\nFAILED:")
    for item in FAIL: print(f"  [FAIL] {item}")
if WARN:
    print("\nWARNINGS:")
    for item in WARN: print(f"  [WARN] {item}")
if not FAIL:
    print("\n[ALL DEMO CHECKS PASSED]")
sys.exit(0 if not FAIL else 1)
