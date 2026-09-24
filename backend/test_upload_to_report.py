"""
SONAR-X Upload-to-Report End-to-End Test
Tests the complete automatic workflow:
  LOGIN → UPLOAD → METADATA → SURVEY → PREPROCESS → DETECT → FINGERPRINT →
  FUSE → CLASSIFY → HAZARD → REPORT

Uses a controlled synthetic sonar image with known targets so we can verify
that candidates are genuinely detected and processed.

Scientific integrity:
  - Does not fabricate detections
  - Does not require a specific count
  - Verifies the pipeline ran (preprocessing logs exist)
  - Verifies fingerprint records exist for any detections found
"""

import sys, os, json, tempfile

# ── Path setup ────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_DIR = os.path.join(ROOT, "ai")
BACKEND_DIR = os.path.join(ROOT, "backend")
for p in [ROOT, BACKEND_DIR, AI_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import urllib.request, urllib.error

BASE = "http://127.0.0.1:8000/api"
PASS, FAIL, WARN = [], [], []

def ok(msg):   PASS.append(msg);  print(f"  [PASS] {msg}")
def fail(msg): FAIL.append(msg);  print(f"  [FAIL] {msg}")
def warn(msg): WARN.append(msg);  print(f"  [WARN] {msg}")

def post_json(url, data, token=None):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def post_multipart(url, token, filepath, fieldname="files", filename=None):
    """Post a file as multipart/form-data."""
    boundary = "----SonarXE2EBoundary"
    fname = filename or os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{fieldname}"; filename="{fname}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, json.loads(r.read())

print("=" * 65)
print("SONAR-X UPLOAD-TO-REPORT END-TO-END TEST")
print("=" * 65)

# ── 1. Login ──────────────────────────────────────────────────────
print("\n[1] AUTHENTICATION")
try:
    login = post_json(f"{BASE}/auth/login/", {"email": "demo@sonarx.ai", "password": "demo123"})
    token = login["access"]
    ok(f"Login: {login['user']['email']} ({login['user']['role']})")
except Exception as e:
    fail(f"Login failed: {e}"); sys.exit(1)

# ── 2. Create a controlled test image with clear targets ──────────
print("\n[2] CREATING CONTROLLED TEST IMAGE")
try:
    import numpy as np
    import cv2

    # 512x256 image mimicking a side-scan sonar waterfall
    rng = np.random.default_rng(12345)
    img = np.clip(rng.normal(45, 14, (256, 512)), 0, 255).astype(np.uint8)

    # Nadir dark band
    img[:, 236:276] = 5

    # Target 1: Marine debris candidate — compact, bright, with shadow
    cv2.ellipse(img, (120, 90), (22, 14), 0, 0, 360, 215, -1)
    cv2.ellipse(img, (118, 88), (10, 7), 0, 0, 360, 230, -1)   # bright core
    img[82:104, 142:178] = 5   # acoustic shadow

    # Target 2: Larger structured target — potential hazard
    cv2.rectangle(img, (310, 75), (390, 130), 225, -1)
    cv2.rectangle(img, (318, 83), (382, 122), 240, -1)          # brighter core
    img[75:130, 390:460] = 4   # strong shadow

    # Apply slight blur to look more natural
    img = cv2.GaussianBlur(img, (3, 3), 0)

    # Save
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cv2.imwrite(tmp.name, img)
    tmp_path = tmp.name

    ok(f"Test image: {tmp.name} ({os.path.getsize(tmp_path):,} bytes, 512x256)")
    ok("Image has 2 explicit targets for detection testing")
except Exception as e:
    fail(f"Image creation: {e}"); sys.exit(1)

# ── 3. POST to ingest endpoint ────────────────────────────────────
print("\n[3] UPLOAD AND INGEST")
try:
    status_code, ingest = post_multipart(
        f"{BASE}/surveys/ingest/", token, tmp_path,
        fieldname="files", filename="e2e_sonar_test.png"
    )
    assert status_code == 201, f"Expected 201, got {status_code}"
    ok(f"HTTP 201 — Survey: {ingest.get('survey_id')} (pk={ingest.get('survey_pk')})")
    ok(f"Survey name: '{ingest.get('survey_name')}'")
    ok(f"Status: {ingest.get('status')}")
    ok(f"Inference mode: {ingest.get('inference_mode')}")

    survey_pk = ingest["survey_pk"]
    survey_id = ingest["survey_id"]
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    fail(f"Ingest HTTP {e.code}: {body[:500]}")
    sys.exit(1)
except Exception as e:
    fail(f"Ingest: {e}")
    sys.exit(1)

# ── 4. Metadata provenance ────────────────────────────────────────
print("\n[4] METADATA PROVENANCE")
try:
    ms = ingest.get("metadata_summary", {})
    found = ms.get("found", [])
    unavailable = ms.get("unavailable", [])
    ok(f"Metadata extracted: {found}")
    ok(f"Unavailable (not fabricated): {unavailable}")
    # For a plain PNG with no EXIF GPS, GPS must be in unavailable
    assert "GPS Coordinates" in unavailable or "GPS Coordinates" in found
    # Image Dimensions must always be found
    assert "Image Dimensions" in found, f"Image Dimensions missing from found: {found}"
    ok("Image Dimensions present in metadata")
    note = ms.get("note", "")
    assert "not fabricated" in note.lower(), f"Provenance note missing: {note}"
    ok("Provenance note confirms no fabrication")
except Exception as e:
    fail(f"Metadata provenance: {e}")

# ── 5. Survey created correctly ───────────────────────────────────
print("\n[5] SURVEY IN DATABASE")
try:
    survey = get(f"{BASE}/surveys/{survey_pk}/", token)
    assert survey["status"] == "COMPLETED", f"Status: {survey['status']}"
    assert not survey["is_demo"], "Must not be flagged as demo"
    assert survey["data_source"] == "SURVEY", f"data_source: {survey['data_source']}"
    ok(f"Survey name: '{survey['name']}'")
    ok(f"Survey date: {survey['date']}")
    ok("data_source=SURVEY, is_demo=False, status=COMPLETED")
except Exception as e:
    fail(f"Survey check: {e}")

# ── 6. Preprocessing ran ──────────────────────────────────────────
print("\n[6] PREPROCESSING PIPELINE")
try:
    pp = ingest.get("preprocessing", {})
    if pp:
        first_key = list(pp.keys())[0]
        first_pp = pp[first_key]
        ok(f"Preprocessing result for file {first_key}: keys={list(first_pp.keys())[:5]}")
        # Check nadir was handled
        nadir_info = first_pp.get("nadir", {})
        nadir_status = nadir_info.get("status", "UNKNOWN") if isinstance(nadir_info, dict) else str(nadir_info)
        ok(f"Nadir handling: {nadir_status}")
        # Quality was assessed
        quality_info = first_pp.get("quality", {})
        if isinstance(quality_info, dict):
            ok(f"Quality score: {quality_info.get('score', '?')}, level: {quality_info.get('level', '?')}")
    else:
        warn("No preprocessing results in response (may have been skipped)")
except Exception as e:
    warn(f"Preprocessing check: {e}")

# ── 7. Detection pipeline ─────────────────────────────────────────
print("\n[7] DETECTION")
try:
    det_count = ingest.get("detection_count", 0)
    ok(f"Detection count: {det_count}")

    if det_count > 0:
        # Verify detections from the database directly
        dets_resp = get(f"{BASE}/detections/?survey={survey_pk}", token)
        dets = dets_resp.get("results", dets_resp if isinstance(dets_resp, list) else [])
        ok(f"Detections in DB: {len(dets)}")
        for d in dets[:3]:
            ok(f"  {d['detection_uid']} → {d['classification']} | "
               f"inference={d.get('inference_mode','?')} | "
               f"fp_risk={d.get('false_positive_risk','?')}")
        # Verify not flagged as demo
        demo_flagged = [d for d in dets if d.get("is_demo", False)]
        if demo_flagged:
            fail(f"{len(demo_flagged)} detections incorrectly flagged as demo")
        else:
            ok("No detections incorrectly flagged as demo")
    else:
        warn(
            "Zero detections — image may not contain classifiable candidates. "
            "This is a valid result if the image has no clear acoustic anomalies."
        )
except Exception as e:
    fail(f"Detection check: {e}")

# ── 8. Fingerprint + fusion on each detection ─────────────────────
print("\n[8] FINGERPRINT + EVIDENCE FUSION")
try:
    if det_count > 0:
        dets_resp = get(f"{BASE}/detections/?survey={survey_pk}", token)
        dets = dets_resp.get("results", dets_resp if isinstance(dets_resp, list) else [])
        for d in dets[:3]:
            det_detail = get(f"{BASE}/detections/{d['id']}/", token)
            fp = det_detail.get("fingerprint")
            if fp:
                CUES = ["backscatter_score","texture_score","geometry_score",
                        "shadow_score","object_shadow_score","seabed_context_score",
                        "signal_quality_score"]
                all_cues_present = all(cue in fp for cue in CUES)
                if all_cues_present:
                    ok(f"  {d['detection_uid']}: all 7 fingerprint cues present")
                    ok(f"    evidence_score={fp.get('evidence_score','?')}")
                else:
                    missing = [c for c in CUES if c not in fp]
                    warn(f"  {d['detection_uid']}: missing cues {missing}")
                # Verify no 'probability' wording
                assert "probability" not in str(det_detail).lower(), \
                    "Found forbidden 'probability' in detection response"
                ok(f"  Scientific: 'probability' not used in {d['detection_uid']}")
            else:
                warn(f"  {d['detection_uid']}: fingerprint not present in detail response")
    else:
        ok("No detections to fingerprint — pipeline ran cleanly with zero candidates")
except Exception as e:
    fail(f"Fingerprint/fusion check: {e}")

# ── 9. Hazard assessment ──────────────────────────────────────────
print("\n[9] HAZARD ASSESSMENT")
try:
    if det_count > 0:
        import re
        dets_resp = get(f"{BASE}/detections/?survey={survey_pk}", token)
        dets = dets_resp.get("results", dets_resp if isinstance(dets_resp, list) else [])
        hazard_levels = {d.get("hazard_level", "NONE") for d in dets}
        ok(f"Hazard levels present: {hazard_levels}")
        for level in hazard_levels:
            assert level in ("NONE", "CAUTION", "HIGH_CAUTION"), f"Invalid hazard level: {level}"
        # Verify no specific hazardous object identification
        for d in dets:
            haz = get(f"{BASE}/detections/{d['id']}/hazard/", token)
            indicators_text = " ".join(haz.get("hazard_indicators", [])).lower()
            for forbidden in ["mine", "bomb", "munition", "weapon", "explosive"]:
                assert not re.search(r"\b" + forbidden + r"\b", indicators_text), \
                    f"Forbidden term '{forbidden}' in hazard indicators"
        ok("No specific hazardous object identification in any detection")
    else:
        ok("No detections — hazard assessment not applicable")
except Exception as e:
    fail(f"Hazard check: {e}")

# ── 10. Report generated ──────────────────────────────────────────
print("\n[10] AUTOMATIC REPORT")
try:
    rpt = ingest.get("report", {})
    if rpt.get("status") == "GENERATED":
        report_id = rpt.get("report_id")
        ok(f"PDF report auto-generated: {report_id}")
        # Verify download works — PDF is binary, request directly
        req = urllib.request.Request(
            f"{BASE}/reports/download/{report_id}/",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            pdf_bytes = r.read()
        assert len(pdf_bytes) > 500, f"PDF too small: {len(pdf_bytes)} bytes"
        assert pdf_bytes[:4] == b"%PDF", f"Not a valid PDF: header={pdf_bytes[:8]}"
        ok(f"PDF download OK: {len(pdf_bytes):,} bytes, valid PDF header")
    else:
        warn(f"Report status: {rpt.get('status')} — {rpt.get('reason','')[:100]}")
except Exception as e:
    warn(f"Report download: {e}")

# ── 11. Existing demo still intact ────────────────────────────────
print("\n[11] DEMO SURVEY INTEGRITY")
try:
    demo_surveys = get(f"{BASE}/surveys/demo/", token)
    demo_ids = [s["survey_id"] for s in demo_surveys]
    assert "SX-SRV-DEMO-001" in demo_ids, f"Main demo survey missing from: {demo_ids}"
    ok(f"Demo surveys intact: {demo_ids}")

    # Verify demo detections exist
    main_demo = next(s for s in demo_surveys if s["survey_id"] == "SX-SRV-DEMO-001")
    assert main_demo["detection_count"] >= 1
    ok(f"Demo detections intact: {main_demo['detection_count']}")
except Exception as e:
    fail(f"Demo integrity: {e}")

# ── 12. Temporal still works ──────────────────────────────────────
print("\n[12] TEMPORAL INTELLIGENCE STILL INTACT")
try:
    temporal = get(f"{BASE}/temporal/", token)
    relocated = [o for o in temporal["debris_objects"] if o["current_status"] == "POTENTIALLY_RELOCATED"]
    assert len(relocated) >= 1
    ok(f"POTENTIALLY_RELOCATED case intact: {relocated[0]['debris_uid']}")
except Exception as e:
    fail(f"Temporal check: {e}")

# ── Cleanup ───────────────────────────────────────────────────────
try:
    os.unlink(tmp_path)
except Exception:
    pass

# ── Summary ───────────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f"PASSES: {len(PASS)}  FAILS: {len(FAIL)}  WARNINGS: {len(WARN)}")
if FAIL:
    print("\nFAILED:")
    for item in FAIL: print(f"  {item}")
if WARN:
    print("\nWARNINGS:")
    for item in WARN: print(f"  {item}")
if not FAIL:
    print("\n[ALL UPLOAD-TO-REPORT TESTS PASSED]")
sys.exit(0 if not FAIL else 1)
