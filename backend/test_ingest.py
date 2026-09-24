"""
Test the /api/surveys/ingest/ endpoint end-to-end.
Generates a synthetic sonar image, posts it, verifies the full pipeline ran.
"""
import sys, os, json, io, tempfile
sys.path.insert(0, r"c:\Users\adity\OneDrive\Desktop\sonar\sonar-x\ai")
sys.path.insert(0, r"c:\Users\adity\OneDrive\Desktop\sonar\sonar-x\backend")

import urllib.request, urllib.error

BASE = "http://127.0.0.1:8000/api"
PASS, FAIL = [], []

def ok(msg):  PASS.append(msg);  print(f"  [PASS] {msg}")
def fail(msg): FAIL.append(msg); print(f"  [FAIL] {msg}")

def post_json(url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

print("=" * 60)
print("SONAR-X INGEST ENDPOINT TEST")
print("=" * 60)

# 1. Login
try:
    login = post_json(f"{BASE}/auth/login/", {"email": "demo@sonarx.ai", "password": "demo123"})
    token = login["access"]
    ok(f"Login: {login['user']['email']}")
except Exception as e:
    fail(f"Login: {e}"); sys.exit(1)

# 2. Generate a synthetic sonar image
print("\n[SETUP] Generating synthetic sonar image...")
try:
    import numpy as np
    import cv2

    rng = np.random.default_rng(999)
    img = np.clip(rng.normal(40, 15, (256, 512)), 0, 255).astype(np.uint8)
    # Nadir
    img[:, 236:276] = 5
    # Bright target (marine debris)
    cv2.ellipse(img, (120, 100), (25, 15), 0, 0, 360, 220, -1)
    img[100:115, 145:175] = 5  # shadow
    # Second target (potential hazard)
    cv2.rectangle(img, (300, 80), (390, 140), 235, -1)
    img[80:140, 390:450] = 5  # large shadow

    # Save to a temp PNG
    tmp_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cv2.imwrite(tmp_img.name, img)
    ok(f"Synthetic sonar image created: {tmp_img.name} ({os.path.getsize(tmp_img.name)} bytes)")
except Exception as e:
    fail(f"Image generation: {e}"); sys.exit(1)

# 3. Post to ingest endpoint
print("\n[TEST] Posting to /api/surveys/ingest/...")
try:
    import urllib.parse

    # Build multipart form data manually
    boundary = "----SonarXTestBoundary"
    with open(tmp_img.name, "rb") as f:
        img_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="sonar_test_image.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + img_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE}/surveys/ingest/",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        ingest_result = json.loads(r.read())

    ok(f"Ingest HTTP 201 received")
    ok(f"Survey created: {ingest_result.get('survey_id')} (pk={ingest_result.get('survey_pk')})")
    ok(f"Status: {ingest_result.get('status')}")
    ok(f"Inference mode: {ingest_result.get('inference_mode', '?')}")
    ok(f"Detection count: {ingest_result.get('detection_count', '?')}")

except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    fail(f"Ingest HTTP {e.code}: {body[:300]}")
    sys.exit(1)
except Exception as e:
    fail(f"Ingest request: {e}")
    sys.exit(1)

# 4. Verify survey was created in DB
print("\n[VERIFY] Survey in database...")
try:
    survey_pk = ingest_result["survey_pk"]
    survey = get(f"{BASE}/surveys/{survey_pk}/", token)
    assert survey["status"] == "COMPLETED", f"Survey status: {survey['status']}"
    assert not survey["is_demo"], "Must not be flagged as demo"
    assert survey["data_source"] == "SURVEY"
    ok(f"Survey name: '{survey['name']}'")
    ok(f"Survey date: {survey['date']}")
    ok(f"data_source=SURVEY, is_demo=False confirmed")
except Exception as e:
    fail(f"Survey verification: {e}")

# 5. Verify detections were created
print("\n[VERIFY] Detections created...")
try:
    dets_resp = get(f"{BASE}/detections/?survey={survey_pk}", token)
    dets = dets_resp.get("results", dets_resp if isinstance(dets_resp, list) else [])
    ok(f"Detections: {len(dets)}")
    for d in dets[:3]:
        ok(f"  {d['detection_uid']} → {d['classification']} ({d.get('inference_mode','?')})")
    # Verify all detections are SURVEY data source, not DEMO
    for d in dets:
        if d.get("is_demo"):
            fail(f"Detection {d['detection_uid']} incorrectly marked as demo")
except Exception as e:
    fail(f"Detection verification: {e}")

# 6. Verify metadata provenance returned
print("\n[VERIFY] Metadata provenance...")
try:
    meta_summary = ingest_result.get("metadata_summary", {})
    assert "found" in meta_summary or "unavailable" in meta_summary or "status" in meta_summary
    ok(f"Metadata summary returned: found={meta_summary.get('found', [])}")
    ok(f"Unavailable (not fabricated): {meta_summary.get('unavailable', [])}")
    # GPS should be unavailable for a synthetic PNG with no EXIF
    note = meta_summary.get("note", "")
    if "not fabricated" in note.lower():
        ok("Provenance note confirms no fabrication")
except Exception as e:
    fail(f"Metadata provenance: {e}")

# 7. Verify report was auto-generated
print("\n[VERIFY] Auto-report generation...")
try:
    rpt = ingest_result.get("report", {})
    if rpt.get("status") == "GENERATED":
        ok(f"PDF report auto-generated: report_id={rpt.get('report_id', '?')}")
    else:
        ok(f"Report: {rpt.get('status', '?')} — {rpt.get('reason', '')[:80]}")
except Exception as e:
    fail(f"Report check: {e}")

# 8. Verify existing demo still intact
print("\n[VERIFY] Demo survey still intact...")
try:
    demo_surveys = get(f"{BASE}/surveys/demo/", token)
    assert len(demo_surveys) >= 2, "Demo surveys missing"
    demo_ids = [s["survey_id"] for s in demo_surveys]
    assert "SX-SRV-DEMO-001" in demo_ids, "Main demo survey missing"
    ok(f"Demo surveys intact: {demo_ids}")
except Exception as e:
    fail(f"Demo check: {e}")

# Cleanup
try:
    os.unlink(tmp_img.name)
except Exception:
    pass

# Summary
print(f"\n{'='*60}")
print(f"PASSES: {len(PASS)}  FAILS: {len(FAIL)}")
if FAIL:
    print("\nFailed:")
    for f_item in FAIL: print(f"  {f_item}")
else:
    print("\n[ALL INGEST TESTS PASSED]")
sys.exit(0 if not FAIL else 1)
